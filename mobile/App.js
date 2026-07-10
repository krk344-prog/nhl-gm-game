import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  FlatList,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

const COLORS = {
  bg: '#06111f',
  bg2: '#081a2d',
  card: '#0b2035',
  card2: '#0f2a45',
  line: '#24445f',
  text: '#f4f8ff',
  muted: '#8fa8bd',
  blue: '#2b9dff',
  blueSoft: '#0d4f93',
  green: '#4ee070',
  yellow: '#ffcb3d',
  orange: '#ff9b38',
  red: '#ff4d57',
};

const fallbackTeamState = {
  city: 'New York',
  name: 'Rangers',
  gm: 'You',
  day: 1,
  maxDays: 186,
  nextGame: 'BOS (H)',
  nextDate: 'Oct 6, 2024',
  cash: 25000000,
  capHit: 88250000,
  capCeiling: 92000000,
  accruedCap: 4210000,
  jobSecurity: 70,
  overall: 87,
  offense: 88,
  defense: 86,
  goalies: 84,
  wins: 0,
  losses: 0,
  overtimeLosses: 0,
  points: 0,
};

const fallbackRoster = [
  { id: 34, name: 'C. Hughes', pos: 'C', age: 24, ovr: 84, fog: 14, aav: 8.75, role: 'Elite Playmaker' },
  { id: 16, name: 'A. Barkov', pos: 'C', age: 28, ovr: 92, fog: 12, aav: 9.25, role: 'Two-Way Forward' },
  { id: 10, name: 'A. Panarin', pos: 'LW', age: 33, ovr: 89, fog: 16, aav: 7.0, role: 'Volume Sniper' },
  { id: 24, name: 'K. Kakko', pos: 'RW', age: 23, ovr: 82, fog: 18, aav: 2.1, role: 'Forechecker' },
  { id: 93, name: 'M. Zibanejad', pos: 'C', age: 31, ovr: 88, fog: 13, aav: 8.5, role: 'Power Play Driver' },
  { id: 72, name: 'V. Trocheck', pos: 'C', age: 30, ovr: 81, fog: 15, aav: 5.63, role: 'Two-Way Forward' },
  { id: 77, name: 'B. Wheeler', pos: 'RW', age: 37, ovr: 81, fog: 19, aav: 4.0, role: 'Veteran Leader' },
  { id: 13, name: 'A. Lafrenière', pos: 'LW', age: 23, ovr: 80, fog: 17, aav: 2.33, role: 'Developing Scorer' },
  { id: 50, name: 'W. Cuylle', pos: 'RW', age: 22, ovr: 77, fog: 20, aav: 0.95, role: 'Energy Forward' },
  { id: 22, name: 'J. Brodzinski', pos: 'LW', age: 30, ovr: 76, fog: 19, aav: 0.88, role: 'Depth Forward' },
  { id: 72, name: 'F. Chytil', pos: 'C', age: 25, ovr: 78, fog: 18, aav: 2.3, role: 'Middle Six' },
  { id: 21, name: 'B. Goodrow', pos: 'RW', age: 31, ovr: 77, fog: 16, aav: 3.64, role: 'Penalty Killer' },
];

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || 'The NHL GM API returned an error');
  }
  return payload;
}

function mapDashboard(payload) {
  return {
    ...fallbackTeamState,
    city: payload.team.city,
    name: payload.team.name,
    day: payload.calendar.current_day,
    maxDays: payload.calendar.max_days,
    cash: payload.finances.cash_balance,
    capHit: payload.finances.cap_hit,
    capCeiling: payload.finances.cap_ceiling,
    accruedCap: payload.finances.accrued_deadline_buying_power,
    jobSecurity: Math.round(payload.team.gm_trust_score),
    overall: payload.ratings.overall,
    offense: payload.ratings.offense,
    defense: payload.ratings.defense,
    goalies: payload.ratings.goalies,
    wins: payload.standing?.wins || 0,
    losses: payload.standing?.losses || 0,
    overtimeLosses: payload.standing?.overtime_losses || 0,
    points: payload.standing?.points || 0,
    nextGame: payload.next_game
      ? `${payload.next_game.opponent} (${payload.next_game.venue === 'home' ? 'H' : 'A'})`
      : 'Season complete',
    nextDate: payload.next_game ? `Day ${payload.next_game.day}` : '-',
  };
}

async function fetchGameState() {
  const responses = await Promise.all([
    fetch(`${API_BASE_URL}/teams/1/dashboard`),
    fetch(`${API_BASE_URL}/teams/1/roster`),
  ]);
  if (responses.some((response) => !response.ok)) {
    throw new Error('The NHL GM API returned an error');
  }
  const [dashboardPayload, rosterPayload] = await Promise.all(
    responses.map((response) => response.json()),
  );
  return {
    teamState: mapDashboard(dashboardPayload),
    roster: mapRoster(rosterPayload),
  };
}

function mapRoster(payload) {
  return payload.players.map((player) => ({
    id: player.id,
    name: player.name,
    pos: player.position,
    age: player.age,
    ovr: player.overall,
    fog: Math.round(player.scouting_uncertainty),
    aav: player.aav / 1000000,
    role: player.archetype,
  }));
}

const gameLog = [
  { period: '1ST', time: '04:00', team: 'NYR', title: 'GOAL (NYR)', detail: 'A. Barkov (2) Assist: C. Hughes, M. Zibanejad', score: '1-0' },
  { period: '1ST', time: '17:00', team: 'BOS', title: 'GOAL (BOS)', detail: 'N. Pastrnak (3) Assist: B. Marchand', score: '1-1' },
  { period: '2ND', time: '11:00', team: 'NYR', title: 'GOAL (NYR)', detail: 'C. Hughes (3) Assist: A. Panarin', score: '2-1' },
  { period: '3RD', time: '08:00', team: 'BOS', title: 'GOAL (BOS)', detail: 'D. Krejci (1) Assist: P. Zacha', score: '2-2' },
];

const officeItems = [
  { icon: '🧢', title: 'Coaching Staff', detail: 'System Fit: 83% • 1-2-2 Aggressive' },
  { icon: '🔎', title: 'Scouting', detail: '12 Active Scouts • Global Coverage: 78%' },
  { icon: '🏥', title: 'Injury Report', detail: '2 Injured Players • 1 on LTIR' },
  { icon: '🛫', title: 'Waiver Wire', detail: '3 Players Available • Priority: 18' },
  { icon: '💵', title: 'Business Operations', detail: 'Revenue: $128.4M • Profit: $18.7M' },
  { icon: '❤️', title: 'Fan Volatility', detail: 'FVI: 42/100 • Mood: Hopeful' },
  { icon: '🤝', title: 'GM Relationships', detail: 'League Trust: 72.5 • R_ij Network View' },
];

function money(value) {
  return `$${value.toFixed(2)}M`;
}

function Header({ title, subtitle }) {
  return (
    <View style={styles.header}>
      <Text style={styles.headerButton}>☰</Text>
      <View style={styles.headerTitleWrap}>
        <Text style={styles.logoText}>{title}</Text>
        {subtitle ? <Text style={styles.headerSubtitle}>{subtitle}</Text> : null}
      </View>
      <Text style={styles.headerButton}>✉</Text>
    </View>
  );
}

function ScreenTitle({ title, action = '⋮' }) {
  return (
    <View style={styles.screenTitleRow}>
      <Text style={styles.backArrow}>‹</Text>
      <Text style={styles.screenTitle}>{title}</Text>
      <Text style={styles.headerButton}>{action}</Text>
    </View>
  );
}

function ProgressBar({ value, max = 100, color = COLORS.blue }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <View style={styles.progressTrack}>
      <View style={[styles.progressFill, { width: `${pct}%`, backgroundColor: color }]} />
    </View>
  );
}

function Card({ children, style }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

function MetricCard({ label, value, sub, color = COLORS.text }) {
  return (
    <Card style={styles.metricCard}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={[styles.metricValue, { color }]}>{value}</Text>
      {sub ? <Text style={styles.metricSub}>{sub}</Text> : null}
    </Card>
  );
}

function TeamBadge({ abbrev, color = COLORS.blue }) {
  return (
    <View style={[styles.teamBadge, { borderColor: color }]}> 
      <Text style={[styles.teamBadgeText, { color }]}>{abbrev}</Text>
    </View>
  );
}

function SyncStatus({ status }) {
  const live = status === 'live';
  const label = status === 'loading' ? 'SYNCING GAME STATE' : live ? 'LIVE DATABASE' : 'OFFLINE DEMO DATA';
  return <Text style={[styles.syncStatus, { color: live ? COLORS.green : COLORS.yellow }]}>{label}</Text>;
}

function DashboardScreen({ teamState, syncStatus, onAdvanceDay, advancing, actionMessage }) {
  const capSpace = (teamState.capCeiling - teamState.capHit) / 1000000;
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <Header title="NHL GM" subtitle="GAME" />
      <SyncStatus status={syncStatus} />

      <Card style={styles.heroCard}>
        <View style={styles.teamHeroRow}>
          <TeamBadge abbrev="NYR" />
          <View style={styles.teamHeroText}>
            <Text style={styles.cityText}>{teamState.city}</Text>
            <Text style={styles.teamName}>{teamState.name}</Text>
            <Text style={styles.muted}>GM: {teamState.gm}</Text>
            <Text style={styles.muted}>Job Security: {teamState.jobSecurity}/100</Text>
            <Text style={styles.muted}>Record: {teamState.wins}-{teamState.losses}-{teamState.overtimeLosses} · {teamState.points} PTS</Text>
            <ProgressBar value={teamState.jobSecurity} color={COLORS.green} />
          </View>
        </View>
      </Card>

      <View style={styles.twoCol}>
        <Card style={styles.splitCard}>
          <Text style={styles.label}>DAY {String(teamState.day).padStart(3, '0')} / {teamState.maxDays}</Text>
          <Text style={styles.valueSmall}>Regular Season</Text>
        </Card>
        <Card style={styles.splitCard}>
          <Text style={styles.label}>NEXT GAME</Text>
          <Text style={styles.valueSmall}>vs {teamState.nextGame}</Text>
          <Text style={styles.muted}>{teamState.nextDate}</Text>
        </Card>
      </View>

      <View style={styles.twoCol}>
        <MetricCard label="CAP SPACE" value={money(capSpace)} sub={`${money(teamState.capHit / 1000000)} / ${money(teamState.capCeiling / 1000000)}`} color={COLORS.text} />
        <MetricCard label="ACCRUED CAP SPACE" value={money(teamState.accruedCap / 1000000)} sub="Deadline Buying Power" color={COLORS.text} />
      </View>

      <View style={styles.fourCol}>
        <SmallRating label="TEAM" value={teamState.overall} icon="🛡" />
        <SmallRating label="OFFENSE" value={teamState.offense} icon="🏒" />
        <SmallRating label="DEFENSE" value={teamState.defense} icon="🧱" />
        <SmallRating label="GOALIES" value={teamState.goalies} icon="🥅" />
      </View>

      <Text style={styles.sectionTitle}>QUICK ACTIONS</Text>
      <ActionRow icon="📅" title={advancing ? 'Advancing...' : 'Advance Day'} detail="Settle cap charges and simulate the league slate" onPress={onAdvanceDay} disabled={advancing || syncStatus !== 'live'} />
      {actionMessage ? <Text style={styles.actionMessage}>{actionMessage}</Text> : null}
      <ActionRow icon="▶" title="Sim Today's Game" detail="vs BOS" />
      <ActionRow icon="🔁" title="Trade Center" detail="Propose or Review Trades" />
      <ActionRow icon="👓" title="Scout Players" detail="Reduce Fog of War" />
    </ScrollView>
  );
}

function SmallRating({ label, value, icon }) {
  return (
    <Card style={styles.smallRating}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.ratingValue}>{value}</Text>
      <Text style={styles.ratingIcon}>{icon}</Text>
    </Card>
  );
}

function ActionRow({ icon, title, detail, onPress, disabled = false }) {
  return (
    <TouchableOpacity activeOpacity={0.85} style={[styles.actionRow, disabled && styles.actionRowDisabled]} onPress={onPress} disabled={disabled}>
      <Text style={styles.actionIcon}>{icon}</Text>
      <View style={styles.actionTextWrap}>
        <Text style={styles.actionTitle}>{title}</Text>
        <Text style={styles.actionDetail}>{detail}</Text>
      </View>
      <Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
  );
}

function RosterScreen({ roster, teamState, syncStatus }) {
  const [section, setSection] = useState('NHL ROSTER');
  return (
    <View style={styles.flex}>
      <ScreenTitle title="ROSTER" action="⌕" />
      <SyncStatus status={syncStatus} />
      <View style={styles.segmented}>
        {['NHL ROSTER', 'AHL AFFILIATE', 'CONTRACTS'].map((item) => (
          <TouchableOpacity key={item} onPress={() => setSection(item)} style={[styles.segmentButton, section === item && styles.segmentActive]}>
            <Text style={[styles.segmentText, section === item && styles.segmentTextActive]}>{item}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Card style={styles.rosterHeaderCard}>
        <View>
          <Text style={styles.sectionTitle}>NHL ROSTER ({roster.length}/23)</Text>
          <Text style={styles.muted}>Fog-of-war uncertainty shown as ± scouting range</Text>
        </View>
        <View style={styles.rightAlign}>
          <Text style={styles.label}>CAP HIT</Text>
          <Text style={styles.valueSmall}>{money(teamState.capHit / 1000000)}</Text>
        </View>
      </Card>

      <View style={styles.rosterTabs}>
        <Text style={[styles.rosterTab, styles.rosterTabActive]}>FORWARDS</Text>
        <Text style={styles.rosterTab}>DEFENSE</Text>
        <Text style={styles.rosterTab}>GOALIES</Text>
      </View>

      <View style={styles.tableHeader}>
        <Text style={[styles.th, { flex: 0.5 }]}>#</Text>
        <Text style={[styles.th, { flex: 2.1 }]}>PLAYER</Text>
        <Text style={[styles.th, { flex: 0.6 }]}>POS</Text>
        <Text style={[styles.th, { flex: 0.6 }]}>AGE</Text>
        <Text style={[styles.th, { flex: 0.8 }]}>OVR</Text>
        <Text style={[styles.th, { flex: 1.0, textAlign: 'right' }]}>AAV</Text>
      </View>

      <FlatList
        data={roster}
        keyExtractor={(item, index) => `${item.id}-${index}`}
        contentContainerStyle={styles.listPad}
        renderItem={({ item, index }) => (
          <View style={styles.tableRow}>
            <Text style={[styles.td, { flex: 0.5 }]}>{index + 1}</Text>
            <View style={{ flex: 2.1 }}>
              <Text style={styles.playerName}>{item.name}</Text>
              <Text style={styles.playerRole}>{item.role}</Text>
            </View>
            <Text style={[styles.td, { flex: 0.6 }]}>{item.pos}</Text>
            <Text style={[styles.td, { flex: 0.6 }]}>{item.age}</Text>
            <View style={{ flex: 0.8 }}>
              <Text style={styles.ovr}>{item.ovr}</Text>
              <Text style={styles.fog}>± {item.fog}</Text>
            </View>
            <Text style={[styles.td, { flex: 1.0, textAlign: 'right' }]}>${item.aav.toFixed(2)}M</Text>
          </View>
        )}
      />
    </View>
  );
}

function GamesScreen() {
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <ScreenTitle title="GAME SIMULATION" />
      <Card style={styles.scoreCard}>
        <View style={styles.scoreRow}>
          <View style={styles.centeredTeam}>
            <TeamBadge abbrev="NYR" />
            <Text style={styles.teamAbbrev}>NYR</Text>
          </View>
          <View style={styles.scoreBlock}>
            <Text style={styles.scoreNumber}>2</Text>
            <Text style={styles.finalText}>FINAL</Text>
            <Text style={styles.finalText}>60:00</Text>
          </View>
          <Text style={styles.scoreDash}>-</Text>
          <View style={styles.scoreBlock}>
            <Text style={styles.scoreNumber}>2</Text>
            <Text style={styles.finalText}>BOS</Text>
          </View>
          <View style={styles.centeredTeam}>
            <TeamBadge abbrev="BOS" color={COLORS.yellow} />
            <Text style={styles.teamAbbrev}>BOS</Text>
          </View>
        </View>

        <View style={styles.statCompareRow}>
          <Text style={styles.valueSmall}>34</Text>
          <Text style={styles.label}>SHOTS ON GOAL</Text>
          <Text style={styles.valueSmall}>26</Text>
        </View>
        <View style={styles.compareTrack}>
          <View style={[styles.compareFill, { width: '56%' }]} />
          <View style={[styles.compareFillAway, { width: '44%' }]} />
        </View>
        <View style={styles.statCompareRow}>
          <Text style={styles.valueSmall}>56%</Text>
          <Text style={styles.label}>POSSESSION (CORSI)</Text>
          <Text style={styles.valueSmall}>44%</Text>
        </View>
      </Card>

      <View style={styles.segmented}>
        {['GAME LOG', 'PERIOD SUMMARY', 'PLAYER STATS'].map((item, index) => (
          <View key={item} style={[styles.segmentButton, index === 0 && styles.segmentActive]}>
            <Text style={[styles.segmentText, index === 0 && styles.segmentTextActive]}>{item}</Text>
          </View>
        ))}
      </View>

      <Card style={styles.logCard}>
        {gameLog.map((play, index) => (
          <View key={`${play.period}-${play.time}-${index}`} style={styles.playRow}>
            <Text style={styles.playTime}>{play.time}</Text>
            <View style={styles.playMiddle}>
              <Text style={styles.playTitle}>{play.title}</Text>
              <Text style={styles.playDetail}>{play.detail}</Text>
            </View>
            <Text style={[styles.playScore, { color: play.team === 'NYR' ? COLORS.blue : COLORS.yellow }]}>{play.score}</Text>
          </View>
        ))}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>GAME RESULTS</Text>
        <View style={styles.twoColLoose}>
          <Text style={styles.bullet}>• Corsi For: 56%</Text>
          <Text style={styles.bullet}>• Faceoffs Won: 52%</Text>
          <Text style={styles.bullet}>• Power Play: 1/3</Text>
          <Text style={styles.bullet}>• Hits: 28</Text>
          <Text style={styles.bullet}>• Penalty Kill: 2/2</Text>
          <Text style={styles.bullet}>• Blocks: 18</Text>
        </View>
      </Card>
    </ScrollView>
  );
}

function TradeScreen({ onTradeComplete }) {
  const [market, setMarket] = useState(null);
  const [offeredIndex, setOfferedIndex] = useState(0);
  const [targetIndex, setTargetIndex] = useState(0);
  const [analysis, setAnalysis] = useState(null);
  const [tradeStatus, setTradeStatus] = useState('loading');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  const loadMarket = useCallback(async () => {
    const payload = await requestJson('/trade-market?user_team_id=1');
    setMarket(payload);
    setOfferedIndex(0);
    setTargetIndex(0);
    setTradeStatus('live');
    return payload;
  }, []);

  useEffect(() => {
    loadMarket().catch((error) => {
      setTradeStatus('offline');
      setMessage(error.message);
    });
  }, [loadMarket]);

  const offeredPlayer = market?.offered_players?.[offeredIndex];
  const targetPlayer = market?.target_players?.[targetIndex];
  const targetTeam = market?.target_team;

  useEffect(() => {
    if (!offeredPlayer || !targetPlayer || !targetTeam) return undefined;
    let active = true;
    setAnalysis(null);
    requestJson('/trades/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        user_team_id: market.user_team.id,
        offered_player_id: offeredPlayer.id,
        target_team_id: targetTeam.id,
        target_player_id: targetPlayer.id,
      }),
    })
      .then((payload) => {
        if (active) setAnalysis(payload);
      })
      .catch((error) => {
        if (active) setMessage(error.message);
      });
    return () => {
      active = false;
    };
  }, [market, offeredPlayer, targetPlayer, targetTeam]);

  const cyclePlayer = (side) => {
    setMessage('');
    if (side === 'offered') {
      setOfferedIndex((index) => (index + 1) % market.offered_players.length);
    } else {
      setTargetIndex((index) => (index + 1) % market.target_players.length);
    }
  };

  const submitTrade = async () => {
    if (!analysis || submitting) return;
    setSubmitting(true);
    setMessage('');
    try {
      const result = await requestJson('/trades/execute', {
        method: 'POST',
        body: JSON.stringify({
          user_team_id: market.user_team.id,
          offered_player_id: offeredPlayer.id,
          target_team_id: targetTeam.id,
          target_player_id: targetPlayer.id,
        }),
      });
      setMessage(`TRADE APPROVED: ${result.target.name} acquired for ${result.offered.name}.`);
      await Promise.all([loadMarket(), onTradeComplete?.()]);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setSubmitting(false);
    }
  };

  const valueDelta = analysis?.user_value_delta || 0;
  const valueEdge = valueDelta > 0.5 ? 'YOU WIN' : valueDelta < -0.5 ? 'RIVAL WINS' : 'EVEN VALUE';
  const gaugeColor = analysis?.accepted ? COLORS.green : COLORS.red;

  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <ScreenTitle title="TRADE CENTER" action="⌕" />
      <SyncStatus status={tradeStatus} />
      <View style={styles.segmented}>
        <View style={[styles.segmentButton, styles.segmentActive]}><Text style={[styles.segmentText, styles.segmentTextActive]}>TRADE PROPOSAL</Text></View>
        <View style={styles.segmentButton}><Text style={styles.segmentText}>TRADE HISTORY</Text></View>
      </View>

      {market && offeredPlayer && targetPlayer ? (
        <>
          <Text style={styles.tradeHint}>Tap either player card to cycle through that team's live roster.</Text>
          <TradeAsset title="OFFERING (YOU)" player={offeredPlayer} color={COLORS.blue} onPress={() => cyclePlayer('offered')} />
          <TradeAsset title={`RECEIVING (${targetTeam.name})`} player={targetPlayer} color={COLORS.yellow} onPress={() => cyclePlayer('target')} />
        </>
      ) : (
        <Card><Text style={styles.muted}>{message || 'Loading the live trade market...'}</Text></Card>
      )}

      <Card style={styles.casvCard}>
        <Text style={styles.sectionTitle}>CASV ANALYSIS</Text>
        <View style={styles.casvRow}>
          <View style={styles.centerColumn}>
            <Text style={[styles.label, { color: COLORS.blue }]}>YOUR OFFER</Text>
            <Text style={[styles.metricValue, { color: COLORS.blue }]}>{analysis ? analysis.offered.casv.toFixed(2) : '--'}</Text>
            <Text style={styles.muted}>CASV Value</Text>
          </View>
          <View style={[styles.tradeGauge, { borderColor: gaugeColor }]}>
            <Text style={styles.gaugeMain}>{analysis ? valueEdge : 'ANALYZING'}</Text>
            <Text style={[styles.gaugeDelta, { color: gaugeColor }]}>{analysis ? `${valueDelta >= 0 ? '+' : ''}${valueDelta.toFixed(2)}` : '--'}</Text>
            <Text style={styles.muted}>{analysis?.decision || 'CASV Desk'}</Text>
          </View>
          <View style={styles.centerColumn}>
            <Text style={[styles.label, { color: COLORS.yellow }]}>{targetTeam?.name || 'RIVAL'}</Text>
            <Text style={[styles.metricValue, { color: COLORS.yellow }]}>{analysis ? analysis.target.casv.toFixed(2) : '--'}</Text>
            <Text style={styles.muted}>CASV Value</Text>
          </View>
        </View>
        <View style={styles.twoCol}>
          <MetricCard label="TRADE DIFFICULTY" value={analysis?.difficulty || '--'} color={COLORS.yellow} />
          <MetricCard label="RELATIONSHIP (R_ij)" value={analysis ? `${analysis.relationship_score}/100` : '--'} color={COLORS.red} />
        </View>
        {analysis ? <Text style={styles.tradeStatus}>Rival requires {analysis.required_value.toFixed(2)} CASV after a ×{analysis.premium_multiplier.toFixed(3)} relationship premium.</Text> : null}
      </Card>

      {message ? <Text style={[styles.actionMessage, { color: message.startsWith('TRADE APPROVED') ? COLORS.green : COLORS.red }]}>{message}</Text> : null}
      <TouchableOpacity style={[styles.primaryButton, (!analysis || submitting) && styles.primaryButtonDisabled]} activeOpacity={0.85} onPress={submitTrade} disabled={!analysis || submitting}>
        <Text style={styles.primaryButtonText}>{submitting ? 'SUBMITTING...' : 'SUBMIT TRADE PROPOSAL'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

function TradeAsset({ title, player, color, onPress }) {
  return (
    <TouchableOpacity activeOpacity={0.85} onPress={onPress}>
      <Card style={styles.tradeAsset}>
        <View style={[styles.tradeAssetTop, { backgroundColor: color === COLORS.blue ? COLORS.blueSoft : '#66510c' }]}>
          <Text style={styles.tradeAssetTitle}>{title}</Text>
          <Text style={styles.tradeAssetCap}>CAP HIT: {money(player.aav / 1000000)}</Text>
        </View>
        <View style={styles.tradePlayerRow}>
          <View style={[styles.avatar, { borderColor: color }]}><Text style={styles.avatarText}>🏒</Text></View>
          <View style={styles.tradePlayerText}>
            <Text style={styles.playerName}>#{player.id}  {player.name}</Text>
            <Text style={styles.playerRole}>{player.position} | Age: {player.age} | {player.archetype}</Text>
            <Text style={styles.playerRole}>OVR {player.overall}     AAV {money(player.aav / 1000000)}     {player.contract_years} YEARS LEFT</Text>
          </View>
          <Text style={styles.closeIcon}>›</Text>
        </View>
      </Card>
    </TouchableOpacity>
  );
}

function OfficeScreen() {
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <ScreenTitle title="FRONT OFFICE" />
      <AdvisorPanel compact />
      {officeItems.map((item) => (
        <TouchableOpacity key={item.title} activeOpacity={0.85} style={styles.officeRow}>
          <Text style={styles.officeIcon}>{item.icon}</Text>
          <View style={styles.officeText}>
            <Text style={styles.officeTitle}>{item.title}</Text>
            <Text style={styles.officeDetail}>{item.detail}</Text>
          </View>
          <View style={styles.officeArrow}><Text style={styles.officeArrowText}>›</Text></View>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

function AdvisorPanel({ compact = false }) {
  return (
    <Card style={styles.advisorCard}>
      <Text style={styles.sectionTitle}>AI ADVISOR DESK</Text>
      <View style={styles.riskCircle}>
        <Text style={styles.riskScore}>51.8</Text>
        <Text style={styles.riskOutOf}>/100</Text>
        <Text style={styles.riskLabel}>MODERATE RISK</Text>
      </View>
      {!compact ? null : (
        <View style={styles.riskBars}>
          <RiskRow label="Cap Efficiency" value={72} />
          <RiskRow label="Roster Construction" value={56} />
          <RiskRow label="Player Overpays" value={44} />
          <RiskRow label="GM Relationships" value={72} />
        </View>
      )}
      <Text style={styles.advisorNote}>Minor asset restructuring required before the upcoming Trade Deadline.</Text>
    </Card>
  );
}

function RiskRow({ label, value }) {
  const color = value >= 70 ? COLORS.green : value >= 50 ? COLORS.yellow : COLORS.orange;
  return (
    <View style={styles.riskRow}>
      <Text style={styles.riskRowLabel}>{label}</Text>
      <View style={styles.riskTrack}><View style={[styles.riskFill, { width: `${value}%`, backgroundColor: color }]} /></View>
      <Text style={styles.riskValue}>{value}/100</Text>
    </View>
  );
}

const navItems = [
  { key: 'dashboard', label: 'DASHBOARD', icon: '⌂' },
  { key: 'roster', label: 'ROSTER', icon: '👥' },
  { key: 'games', label: 'GAMES', icon: '🏒' },
  { key: 'trade', label: 'TRADE', icon: '↔' },
  { key: 'office', label: 'OFFICE', icon: '💼' },
];

function BottomNav({ active, onChange }) {
  return (
    <View style={styles.bottomNav}>
      {navItems.map((item) => {
        const selected = item.key === active;
        return (
          <TouchableOpacity key={item.key} style={styles.navItem} onPress={() => onChange(item.key)} activeOpacity={0.8}>
            <Text style={[styles.navIcon, selected && styles.navIconActive]}>{item.icon}</Text>
            <Text style={[styles.navLabel, selected && styles.navLabelActive]}>{item.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [teamState, setTeamState] = useState(fallbackTeamState);
  const [roster, setRoster] = useState(fallbackRoster);
  const [syncStatus, setSyncStatus] = useState('loading');
  const [advancing, setAdvancing] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  const refreshGameState = useCallback(async () => {
    const state = await fetchGameState();
    setTeamState(state.teamState);
    setRoster(state.roster);
    setSyncStatus('live');
  }, []);

  useEffect(() => {
    refreshGameState().catch(() => setSyncStatus('offline'));
  }, [refreshGameState]);

  const handleAdvanceDay = useCallback(async () => {
    if (advancing) return;
    setAdvancing(true);
    setActionMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/advance-day`, { method: 'POST' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Unable to advance the calendar');
      const game = payload.games[0];
      setActionMessage(
        game
          ? `Day ${payload.calendar.current_day}: ${game.away_team} ${game.away_score} · ${game.home_team} ${game.home_score}${game.overtime ? ' (OT)' : ''}`
          : `Day ${payload.calendar.current_day}: no games scheduled`,
      );
      await refreshGameState();
    } catch (error) {
      setActionMessage(error.message || 'Unable to advance the calendar');
    } finally {
      setAdvancing(false);
    }
  }, [advancing, refreshGameState]);

  const content = useMemo(() => {
    if (activeTab === 'roster') return <RosterScreen roster={roster} teamState={teamState} syncStatus={syncStatus} />;
    if (activeTab === 'games') return <GamesScreen />;
    if (activeTab === 'trade') return <TradeScreen onTradeComplete={refreshGameState} />;
    if (activeTab === 'office') return <OfficeScreen />;
    return <DashboardScreen teamState={teamState} syncStatus={syncStatus} onAdvanceDay={handleAdvanceDay} advancing={advancing} actionMessage={actionMessage} />;
  }, [actionMessage, activeTab, advancing, handleAdvanceDay, refreshGameState, roster, syncStatus, teamState]);

  return (
    <SafeAreaView style={styles.appShell}>
      <StatusBar barStyle="light-content" />
      <View style={styles.phoneFrame}>{content}</View>
      <BottomNav active={activeTab} onChange={setActiveTab} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  appShell: { flex: 1, backgroundColor: COLORS.bg },
  phoneFrame: { flex: 1, backgroundColor: COLORS.bg, paddingHorizontal: 10 },
  flex: { flex: 1 },
  scrollBody: { paddingBottom: 24 },
  syncStatus: { fontSize: 10, fontWeight: '900', letterSpacing: 1.2, marginBottom: 8, textAlign: 'right' },
  header: { height: 66, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerButton: { color: COLORS.text, fontSize: 28, fontWeight: '700', width: 38, textAlign: 'center' },
  headerTitleWrap: { alignItems: 'center' },
  logoText: { color: COLORS.text, fontSize: 28, fontWeight: '900', letterSpacing: 1.5, fontStyle: 'italic' },
  headerSubtitle: { color: COLORS.red, fontSize: 12, fontWeight: '900', marginTop: -4, letterSpacing: 2 },
  screenTitleRow: { height: 62, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  backArrow: { color: COLORS.text, fontSize: 42, lineHeight: 42, width: 38 },
  screenTitle: { color: COLORS.text, fontSize: 20, fontWeight: '900', letterSpacing: 1.8 },
  card: { backgroundColor: COLORS.card, borderColor: COLORS.line, borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 10 },
  heroCard: { padding: 14 },
  teamHeroRow: { flexDirection: 'row', alignItems: 'center' },
  teamHeroText: { flex: 1, marginLeft: 14 },
  cityText: { color: COLORS.text, fontSize: 16, textTransform: 'uppercase', letterSpacing: 1.2 },
  teamName: { color: COLORS.text, fontSize: 28, fontWeight: '900', textTransform: 'uppercase' },
  muted: { color: COLORS.muted, fontSize: 12, marginTop: 2 },
  label: { color: COLORS.muted, fontSize: 11, fontWeight: '800', letterSpacing: 0.8, textTransform: 'uppercase' },
  valueSmall: { color: COLORS.text, fontSize: 16, fontWeight: '800', marginTop: 2 },
  twoCol: { flexDirection: 'row', marginHorizontal: -4 },
  splitCard: { flex: 1, marginHorizontal: 4 },
  metricCard: { flex: 1, marginHorizontal: 4, alignItems: 'center' },
  metricLabel: { color: COLORS.muted, fontSize: 10, fontWeight: '800', textTransform: 'uppercase', letterSpacing: 0.7 },
  metricValue: { color: COLORS.text, fontSize: 24, fontWeight: '900', marginTop: 5 },
  metricSub: { color: COLORS.muted, fontSize: 11, marginTop: 4, textAlign: 'center' },
  fourCol: { flexDirection: 'row', marginHorizontal: -3 },
  smallRating: { flex: 1, marginHorizontal: 3, alignItems: 'center', paddingHorizontal: 4 },
  ratingValue: { color: COLORS.text, fontSize: 22, fontWeight: '900', marginTop: 4 },
  ratingIcon: { fontSize: 22, marginTop: 6 },
  sectionTitle: { color: COLORS.text, fontSize: 15, fontWeight: '900', letterSpacing: 1, marginBottom: 8 },
  actionRow: { backgroundColor: COLORS.card, borderColor: COLORS.line, borderWidth: 1, borderRadius: 10, padding: 12, marginBottom: 7, flexDirection: 'row', alignItems: 'center' },
  actionRowDisabled: { opacity: 0.55 },
  actionMessage: { color: COLORS.green, fontSize: 12, lineHeight: 18, marginBottom: 10, paddingHorizontal: 4 },
  actionIcon: { fontSize: 28, width: 42, textAlign: 'center' },
  actionTextWrap: { flex: 1, marginLeft: 8 },
  actionTitle: { color: COLORS.text, fontSize: 16, fontWeight: '700' },
  actionDetail: { color: COLORS.muted, fontSize: 12, marginTop: 2 },
  chevron: { color: COLORS.muted, fontSize: 26 },
  teamBadge: { width: 72, height: 72, borderWidth: 2, borderRadius: 10, justifyContent: 'center', alignItems: 'center', backgroundColor: '#07192b' },
  teamBadgeText: { fontSize: 19, fontWeight: '900' },
  progressTrack: { height: 6, backgroundColor: '#172a3b', borderRadius: 99, overflow: 'hidden', marginTop: 6 },
  progressFill: { height: '100%', borderRadius: 99 },
  segmented: { flexDirection: 'row', borderWidth: 1, borderColor: COLORS.line, borderRadius: 10, overflow: 'hidden', marginBottom: 10 },
  segmentButton: { flex: 1, paddingVertical: 12, alignItems: 'center', backgroundColor: '#071726' },
  segmentActive: { backgroundColor: COLORS.blueSoft },
  segmentText: { color: COLORS.muted, fontSize: 11, fontWeight: '800' },
  segmentTextActive: { color: COLORS.text },
  rosterHeaderCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rightAlign: { alignItems: 'flex-end' },
  rosterTabs: { flexDirection: 'row', marginBottom: 8 },
  rosterTab: { color: COLORS.muted, paddingVertical: 10, paddingHorizontal: 18, fontWeight: '800' },
  rosterTabActive: { color: COLORS.text, backgroundColor: COLORS.blueSoft, borderRadius: 8 },
  tableHeader: { flexDirection: 'row', paddingVertical: 8, paddingHorizontal: 10, borderBottomColor: COLORS.line, borderBottomWidth: 1 },
  th: { color: COLORS.muted, fontSize: 11, fontWeight: '900' },
  listPad: { paddingBottom: 90 },
  tableRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, paddingHorizontal: 10, borderBottomWidth: 1, borderBottomColor: '#102940' },
  td: { color: COLORS.text, fontSize: 13 },
  playerName: { color: COLORS.text, fontSize: 14, fontWeight: '800' },
  playerRole: { color: COLORS.muted, fontSize: 10, marginTop: 2 },
  ovr: { color: COLORS.text, fontSize: 14, fontWeight: '900' },
  fog: { color: COLORS.green, fontSize: 10, fontWeight: '800' },
  scoreCard: { padding: 14 },
  scoreRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 },
  centeredTeam: { alignItems: 'center' },
  teamAbbrev: { color: COLORS.text, fontSize: 12, fontWeight: '900', marginTop: 4 },
  scoreBlock: { alignItems: 'center' },
  scoreNumber: { color: COLORS.text, fontSize: 42, fontWeight: '900' },
  scoreDash: { color: COLORS.muted, fontSize: 28, fontWeight: '900' },
  finalText: { color: COLORS.muted, fontSize: 12, fontWeight: '800' },
  statCompareRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 },
  compareTrack: { flexDirection: 'row', height: 6, borderRadius: 99, overflow: 'hidden', backgroundColor: '#172a3b', marginTop: 8 },
  compareFill: { backgroundColor: COLORS.blue, height: '100%' },
  compareFillAway: { backgroundColor: COLORS.yellow, height: '100%' },
  logCard: { padding: 0, overflow: 'hidden' },
  playRow: { flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#102940', padding: 12 },
  playTime: { color: COLORS.text, width: 52, fontWeight: '800' },
  playMiddle: { flex: 1 },
  playTitle: { color: COLORS.text, fontWeight: '900', fontSize: 13 },
  playDetail: { color: COLORS.muted, fontSize: 11, marginTop: 3 },
  playScore: { fontSize: 19, fontWeight: '900', width: 42, textAlign: 'right' },
  twoColLoose: { flexDirection: 'row', flexWrap: 'wrap' },
  bullet: { color: COLORS.text, width: '50%', fontSize: 13, paddingVertical: 5 },
  tradeAsset: { padding: 0, overflow: 'hidden' },
  tradeHint: { color: COLORS.muted, fontSize: 11, lineHeight: 16, marginBottom: 8, paddingHorizontal: 4 },
  tradeAssetTop: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, paddingHorizontal: 12 },
  tradeAssetTitle: { color: COLORS.text, fontSize: 12, fontWeight: '900' },
  tradeAssetCap: { color: COLORS.text, fontSize: 11, fontWeight: '800' },
  tradePlayerRow: { flexDirection: 'row', alignItems: 'center', padding: 12 },
  avatar: { width: 48, height: 48, borderRadius: 12, borderWidth: 2, alignItems: 'center', justifyContent: 'center', backgroundColor: '#081726' },
  avatarText: { fontSize: 22 },
  tradePlayerText: { flex: 1, marginLeft: 10 },
  closeIcon: { color: COLORS.muted, fontSize: 24 },
  casvCard: { marginTop: 2 },
  casvRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginVertical: 12 },
  centerColumn: { alignItems: 'center', flex: 1 },
  tradeGauge: { width: 112, height: 112, borderRadius: 56, borderWidth: 10, borderColor: COLORS.green, justifyContent: 'center', alignItems: 'center' },
  gaugeMain: { color: COLORS.text, fontSize: 12, fontWeight: '900' },
  gaugeDelta: { color: COLORS.green, fontSize: 25, fontWeight: '900', marginTop: 2 },
  tradeStatus: { color: COLORS.muted, fontSize: 11, lineHeight: 17, marginTop: 9, textAlign: 'center' },
  primaryButton: { backgroundColor: '#168235', borderRadius: 9, paddingVertical: 15, alignItems: 'center', marginTop: 4, marginBottom: 20 },
  primaryButtonDisabled: { opacity: 0.5 },
  primaryButtonText: { color: COLORS.text, fontSize: 16, fontWeight: '900', letterSpacing: 0.8 },
  advisorCard: { alignItems: 'center' },
  riskCircle: { width: 150, height: 150, borderRadius: 75, borderWidth: 14, borderColor: COLORS.yellow, alignItems: 'center', justifyContent: 'center', marginVertical: 8, backgroundColor: '#071626' },
  riskScore: { color: COLORS.yellow, fontSize: 43, fontWeight: '900' },
  riskOutOf: { color: COLORS.muted, fontSize: 13, marginTop: -6 },
  riskLabel: { color: COLORS.yellow, fontSize: 13, fontWeight: '900', marginTop: 4 },
  riskBars: { alignSelf: 'stretch', marginTop: 6 },
  riskRow: { flexDirection: 'row', alignItems: 'center', marginVertical: 5 },
  riskRowLabel: { color: COLORS.text, fontSize: 12, width: 126 },
  riskTrack: { flex: 1, height: 5, backgroundColor: '#172a3b', borderRadius: 99, overflow: 'hidden' },
  riskFill: { height: '100%' },
  riskValue: { color: COLORS.muted, fontSize: 11, width: 48, textAlign: 'right' },
  advisorNote: { color: COLORS.text, fontSize: 13, lineHeight: 19, alignSelf: 'stretch', marginTop: 10 },
  officeRow: { backgroundColor: COLORS.card, borderColor: COLORS.line, borderWidth: 1, borderRadius: 12, padding: 12, marginBottom: 8, flexDirection: 'row', alignItems: 'center' },
  officeIcon: { width: 42, textAlign: 'center', fontSize: 27 },
  officeText: { flex: 1, marginLeft: 10 },
  officeTitle: { color: COLORS.text, fontSize: 15, fontWeight: '900', textTransform: 'uppercase' },
  officeDetail: { color: COLORS.muted, fontSize: 12, marginTop: 2 },
  officeArrow: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#0c642b', alignItems: 'center', justifyContent: 'center' },
  officeArrowText: { color: COLORS.green, fontSize: 22, fontWeight: '900', marginTop: -2 },
  bottomNav: { height: 72, backgroundColor: '#07121f', borderTopWidth: 1, borderTopColor: COLORS.line, flexDirection: 'row', paddingBottom: 6 },
  navItem: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  navIcon: { color: COLORS.muted, fontSize: 21 },
  navIconActive: { color: COLORS.blue },
  navLabel: { color: COLORS.muted, fontSize: 9, fontWeight: '900', marginTop: 4 },
  navLabelActive: { color: COLORS.blue },
});
