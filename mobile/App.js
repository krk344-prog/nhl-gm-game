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
  city: 'Buffalo',
  name: 'Blizzards',
  gm: 'You',
  day: 1,
  maxDays: 186,
  nextGame: 'Schedule unavailable',
  nextDate: '-',
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

const fallbackRoster = [];

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

async function fetchGameState(requestedTeamId) {
  const game = await requestJson('/game');
  const teamId = requestedTeamId || game.user_team_id;
  const [dashboardPayload, rosterPayload, standingsPayload, schedulePayload] = await Promise.all([
    requestJson(`/teams/${teamId}/dashboard`),
    requestJson(`/teams/${teamId}/roster`),
    requestJson('/standings'),
    requestJson(`/schedule?team_id=${teamId}&limit=200`),
  ]);
  return {
    game,
    teamId,
    teamState: mapDashboard(dashboardPayload),
    roster: mapRoster(rosterPayload),
    standings: standingsPayload.standings,
    schedule: schedulePayload.games,
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
    years: player.contract_years,
  }));
}

const officeItems = [
  { icon: '🧢', title: 'Coaching Staff', detail: 'Coming in a future alpha update' },
  { icon: '🔎', title: 'Scouting', detail: 'Coming in a future alpha update' },
  { icon: '🏥', title: 'Injury Report', detail: 'Coming in a future alpha update' },
  { icon: '🛫', title: 'Waiver Wire', detail: 'Coming in a future alpha update' },
  { icon: '💵', title: 'Business Operations', detail: 'Coming in a future alpha update' },
  { icon: '❤️', title: 'Fan Volatility', detail: 'Coming in a future alpha update' },
  { icon: '🤝', title: 'GM Relationships', detail: 'Coming in a future alpha update' },
];

function abbreviation(team) {
  if (!team) return 'NHL';
  return `${team.city?.[0] || ''}${team.name?.slice(0, 2) || ''}`.toUpperCase();
}

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
  const label = status === 'loading' ? 'SYNCING GAME STATE' : live ? 'LIVE DATABASE' : 'API OFFLINE — CHECK LAUNCHER';
  return <Text style={[styles.syncStatus, { color: live ? COLORS.green : COLORS.yellow }]}>{label}</Text>;
}

function TeamSelector({ teams, selectedTeamId, onSelect, disabled = false }) {
  return (
    <View style={styles.selectorWrap}>
      <Text style={styles.label}>CONTROLLED FRANCHISE</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.selectorRow}>
        {teams.map((team) => {
          const selected = team.id === selectedTeamId;
          return (
            <TouchableOpacity key={team.id} onPress={() => onSelect(team.id)} disabled={disabled || selected} style={[styles.teamChip, selected && styles.teamChipActive]}>
              <Text style={[styles.teamChipText, selected && styles.teamChipTextActive]}>{team.city} {team.name}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

function DashboardScreen({ game, teamId, teamState, syncStatus, onAdvanceDay, advancing, actionMessage, onSelectTeam, selectingTeam, onNavigate, onRetry }) {
  const capSpace = (teamState.capCeiling - teamState.capHit) / 1000000;
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <Header title="NHL GM" subtitle="ALPHA 0.2" />
      <SyncStatus status={syncStatus} />
      {syncStatus === 'offline' ? <ActionRow icon="↻" title="Retry Connection" detail="Reconnect to the local game API" onPress={onRetry} /> : null}
      {game?.requires_reset ? <Text style={styles.warningBanner}>Legacy two-team save detected. Use New Game in Front Office to activate the eight-team alpha league.</Text> : null}
      <TeamSelector teams={game?.teams || []} selectedTeamId={teamId} onSelect={onSelectTeam} disabled={selectingTeam || syncStatus !== 'live'} />

      <Card style={styles.heroCard}>
        <View style={styles.teamHeroRow}>
          <TeamBadge abbrev={abbreviation({ city: teamState.city, name: teamState.name })} />
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
      <ActionRow icon="▶" title="Game Center" detail="Live results, recent games, and standings" onPress={() => onNavigate('games')} />
      <ActionRow icon="🔁" title="Trade Center" detail="Propose or review trades" onPress={() => onNavigate('trade')} />
      <ActionRow icon="👓" title="Scouting — Coming Soon" detail="Disabled during Alpha 0.2 testing" disabled />
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
  const [positionFilter, setPositionFilter] = useState('ALL');
  const filteredRoster = positionFilter === 'ALL'
    ? roster
    : roster.filter((player) => player.pos === positionFilter);
  return (
    <View style={styles.flex}>
      <ScreenTitle title="ROSTER" action="⌕" />
      <SyncStatus status={syncStatus} />

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
        {[
          ['ALL', 'ALL'],
          ['F', 'FORWARDS'],
          ['D', 'DEFENSE'],
          ['G', 'GOALIES'],
        ].map(([key, label]) => (
          <TouchableOpacity key={key} onPress={() => setPositionFilter(key)} style={[styles.rosterTabButton, positionFilter === key && styles.rosterTabActive]}>
            <Text style={[styles.rosterTab, positionFilter === key && styles.rosterTabTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
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
        data={filteredRoster}
        keyExtractor={(item, index) => `${item.id}-${index}`}
        contentContainerStyle={styles.listPad}
        renderItem={({ item, index }) => (
          <View style={styles.tableRow}>
            <Text style={[styles.td, { flex: 0.5 }]}>{index + 1}</Text>
            <View style={{ flex: 2.1 }}>
              <Text style={styles.playerName}>{item.name}</Text>
              <Text style={styles.playerRole}>{item.role} · {item.years}Y</Text>
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

function GamesScreen({ teamId, schedule, standings, syncStatus }) {
  const completedGames = [...schedule]
    .filter((game) => game.status === 'completed')
    .sort((a, b) => b.day - a.day || b.id - a.id);
  const latestGame = completedGames[0];
  const nextGame = schedule.find((game) => game.status === 'scheduled');
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <ScreenTitle title="GAME CENTER" />
      <SyncStatus status={syncStatus} />
      {latestGame ? (
        <Card style={styles.scoreCard}>
          <Text style={styles.label}>LATEST RESULT · DAY {latestGame.day}</Text>
          <View style={styles.scoreRow}>
            <View style={styles.centeredTeam}>
              <TeamBadge abbrev={abbreviation({ city: '', name: latestGame.away_team })} />
              <Text style={styles.teamAbbrev}>{latestGame.away_team}</Text>
            </View>
            <View style={styles.scoreBlock}>
              <Text style={styles.scoreNumber}>{latestGame.away_score}</Text>
            </View>
            <View style={styles.scoreBlock}>
              <Text style={styles.finalText}>FINAL{latestGame.overtime ? ' / OT' : ''}</Text>
              <Text style={styles.scoreDash}>–</Text>
            </View>
            <View style={styles.scoreBlock}>
              <Text style={styles.scoreNumber}>{latestGame.home_score}</Text>
            </View>
            <View style={styles.centeredTeam}>
              <TeamBadge abbrev={abbreviation({ city: '', name: latestGame.home_team })} color={COLORS.yellow} />
              <Text style={styles.teamAbbrev}>{latestGame.home_team}</Text>
            </View>
          </View>
          <Text style={styles.tradeStatus}>The full simulation log is persisted with this result.</Text>
        </Card>
      ) : (
        <Card>
          <Text style={styles.sectionTitle}>NO COMPLETED GAMES</Text>
          <Text style={styles.muted}>Advance to the first scheduled game day to generate a live result.</Text>
        </Card>
      )}

      <Card>
        <Text style={styles.sectionTitle}>NEXT GAME</Text>
        <Text style={styles.valueSmall}>{nextGame ? `Day ${nextGame.day}: ${nextGame.away_team} at ${nextGame.home_team}` : 'Regular season complete'}</Text>
      </Card>

      <Text style={styles.sectionTitle}>RECENT RESULTS</Text>
      {completedGames.slice(0, 5).map((game) => {
        const userIsHome = game.home_team_id === teamId;
        const userScore = userIsHome ? game.home_score : game.away_score;
        const opponentScore = userIsHome ? game.away_score : game.home_score;
        const opponent = userIsHome ? game.away_team : game.home_team;
        return (
          <Card key={game.id} style={styles.resultRow}>
            <View>
              <Text style={styles.playerName}>Day {game.day} · {userIsHome ? 'vs' : 'at'} {opponent}</Text>
              <Text style={styles.muted}>{game.overtime ? 'Overtime' : 'Regulation'}</Text>
            </View>
            <Text style={[styles.resultScore, { color: userScore > opponentScore ? COLORS.green : COLORS.red }]}>{userScore}-{opponentScore}</Text>
          </Card>
        );
      })}

      <Text style={styles.sectionTitle}>LEAGUE STANDINGS</Text>
      <View style={styles.standingsHeader}>
        <Text style={[styles.th, { flex: 2.2 }]}>TEAM</Text>
        <Text style={styles.standingCell}>GP</Text>
        <Text style={styles.standingCell}>W</Text>
        <Text style={styles.standingCell}>L</Text>
        <Text style={styles.standingCell}>OTL</Text>
        <Text style={styles.standingCell}>PTS</Text>
      </View>
      {standings.map((team, index) => (
        <View key={team.team_id} style={[styles.standingsRow, team.team_id === teamId && styles.standingsRowActive]}>
          <Text style={[styles.td, { flex: 2.2 }]}>{index + 1}. {team.city} {team.name}</Text>
          <Text style={styles.standingCellValue}>{team.games_played}</Text>
          <Text style={styles.standingCellValue}>{team.wins}</Text>
          <Text style={styles.standingCellValue}>{team.losses}</Text>
          <Text style={styles.standingCellValue}>{team.overtime_losses}</Text>
          <Text style={[styles.standingCellValue, styles.standingPoints]}>{team.points}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

function TradeScreen({ teamId, onTradeComplete }) {
  const [tab, setTab] = useState('proposal');
  const [market, setMarket] = useState(null);
  const [history, setHistory] = useState([]);
  const [offeredIndex, setOfferedIndex] = useState(0);
  const [targetIndex, setTargetIndex] = useState(0);
  const [analysis, setAnalysis] = useState(null);
  const [tradeStatus, setTradeStatus] = useState('loading');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  const loadMarket = useCallback(async (targetTeamId) => {
    const targetQuery = targetTeamId ? `&target_team_id=${targetTeamId}` : '';
    const payload = await requestJson(`/trade-market?user_team_id=${teamId}${targetQuery}`);
    setMarket(payload);
    setOfferedIndex(0);
    setTargetIndex(0);
    setTradeStatus('live');
    return payload;
  }, [teamId]);

  const loadHistory = useCallback(async () => {
    const payload = await requestJson(`/trades/history?user_team_id=${teamId}&limit=50`);
    setHistory(payload.trades);
  }, [teamId]);

  useEffect(() => {
    setTradeStatus('loading');
    Promise.all([loadMarket(), loadHistory()]).catch((error) => {
      setTradeStatus('offline');
      setMessage(error.message);
    });
  }, [loadHistory, loadMarket]);

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
      await Promise.all([loadMarket(targetTeam.id), loadHistory(), onTradeComplete?.()]);
    } catch (error) {
      setMessage(error.message);
      await loadHistory().catch(() => {});
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
        <TouchableOpacity onPress={() => setTab('proposal')} style={[styles.segmentButton, tab === 'proposal' && styles.segmentActive]}><Text style={[styles.segmentText, tab === 'proposal' && styles.segmentTextActive]}>TRADE PROPOSAL</Text></TouchableOpacity>
        <TouchableOpacity onPress={() => setTab('history')} style={[styles.segmentButton, tab === 'history' && styles.segmentActive]}><Text style={[styles.segmentText, tab === 'history' && styles.segmentTextActive]}>TRADE HISTORY</Text></TouchableOpacity>
      </View>

      {tab === 'history' ? (
        <>
          <Text style={styles.sectionTitle}>RECENT PROPOSALS</Text>
          {history.length ? history.map((trade) => (
            <Card key={trade.id}>
              <View style={styles.resultRow}>
                <View style={styles.tradeHistoryText}>
                  <Text style={styles.playerName}>Day {trade.day}: {trade.offered_player} for {trade.target_player}</Text>
                  <Text style={styles.muted}>Partner: {trade.target_team}</Text>
                  <Text style={styles.muted}>{trade.reason}</Text>
                </View>
                <Text style={[styles.tradeHistoryStatus, { color: trade.status === 'approved' ? COLORS.green : trade.status === 'blocked' ? COLORS.orange : COLORS.red }]}>{trade.status.toUpperCase()}</Text>
              </View>
            </Card>
          )) : <Card><Text style={styles.muted}>No proposals have been submitted in this save.</Text></Card>}
        </>
      ) : market && offeredPlayer && targetPlayer ? (
        <>
          <Text style={styles.label}>TRADE PARTNER</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.selectorRow}>
            {market.rivals.map((rival) => (
              <TouchableOpacity key={rival.id} onPress={() => loadMarket(rival.id).catch((error) => setMessage(error.message))} disabled={rival.id === targetTeam.id} style={[styles.teamChip, rival.id === targetTeam.id && styles.teamChipActive]}>
                <Text style={[styles.teamChipText, rival.id === targetTeam.id && styles.teamChipTextActive]}>{rival.city} {rival.name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          <Text style={styles.tradeHint}>Tap either player card to cycle through that team's live roster.</Text>
          <TradeAsset title="OFFERING (YOU)" player={offeredPlayer} color={COLORS.blue} onPress={() => cyclePlayer('offered')} />
          <TradeAsset title={`RECEIVING (${targetTeam.name})`} player={targetPlayer} color={COLORS.yellow} onPress={() => cyclePlayer('target')} />
        </>
      ) : (
        <Card><Text style={styles.muted}>{message || 'Loading the live trade market...'}</Text></Card>
      )}

      {tab === 'proposal' ? <Card style={styles.casvCard}>
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
      </Card> : null}

      {tab === 'proposal' && message ? <Text style={[styles.actionMessage, { color: message.startsWith('TRADE APPROVED') ? COLORS.green : COLORS.red }]}>{message}</Text> : null}
      {tab === 'proposal' ? <TouchableOpacity style={[styles.primaryButton, (!analysis || submitting) && styles.primaryButtonDisabled]} activeOpacity={0.85} onPress={submitTrade} disabled={!analysis || submitting}>
        <Text style={styles.primaryButtonText}>{submitting ? 'SUBMITTING...' : 'SUBMIT TRADE PROPOSAL'}</Text>
      </TouchableOpacity> : null}
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

function OfficeScreen({ game, onResetGame, resetting }) {
  const [resetArmed, setResetArmed] = useState(false);
  const handleReset = async () => {
    if (!resetArmed) {
      setResetArmed(true);
      return;
    }
    await onResetGame();
    setResetArmed(false);
  };
  return (
    <ScrollView contentContainerStyle={styles.scrollBody}>
      <ScreenTitle title="FRONT OFFICE" />
      <Card>
        <Text style={styles.sectionTitle}>LOCAL SAVE</Text>
        <Text style={styles.valueSmall}>{game?.save?.name || 'Alpha Franchise'}</Text>
        <Text style={styles.muted}>Automatically saved · Day {game?.save?.current_day || 1} / {game?.save?.max_days || 186}</Text>
        <Text style={styles.muted}>Seed {game?.save?.seed ?? 7} · Schema v{game?.save?.schema_version || 1}</Text>
        <TouchableOpacity onPress={handleReset} disabled={resetting} style={[styles.resetButton, resetArmed && styles.resetButtonArmed]}>
          <Text style={styles.primaryButtonText}>{resetting ? 'CREATING NEW GAME...' : resetArmed ? 'CONFIRM NEW GAME — ERASE SAVE' : 'NEW GAME / RESET SAVE'}</Text>
        </TouchableOpacity>
        {resetArmed ? <Text style={styles.resetWarning}>Tap again to erase the current local season and create a fresh eight-team league.</Text> : null}
      </Card>

      <Text style={styles.sectionTitle}>PLANNED FRONT-OFFICE SYSTEMS</Text>
      {officeItems.map((item) => (
        <View key={item.title} style={[styles.officeRow, styles.actionRowDisabled]}>
          <Text style={styles.officeIcon}>{item.icon}</Text>
          <View style={styles.officeText}>
            <Text style={styles.officeTitle}>{item.title}</Text>
            <Text style={styles.officeDetail}>{item.detail}</Text>
          </View>
          <Text style={styles.comingSoon}>COMING SOON</Text>
        </View>
      ))}
    </ScrollView>
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
  const [game, setGame] = useState(null);
  const [teamId, setTeamId] = useState(null);
  const [teamState, setTeamState] = useState(fallbackTeamState);
  const [roster, setRoster] = useState(fallbackRoster);
  const [standings, setStandings] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [syncStatus, setSyncStatus] = useState('loading');
  const [advancing, setAdvancing] = useState(false);
  const [selectingTeam, setSelectingTeam] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  const refreshGameState = useCallback(async (requestedTeamId) => {
    const state = await fetchGameState(requestedTeamId);
    setGame(state.game);
    setTeamId(state.teamId);
    setTeamState(state.teamState);
    setRoster(state.roster);
    setStandings(state.standings);
    setSchedule(state.schedule);
    setSyncStatus('live');
    return state;
  }, []);

  useEffect(() => {
    refreshGameState().catch(() => setSyncStatus('offline'));
  }, [refreshGameState]);

  const handleRetry = useCallback(() => {
    setSyncStatus('loading');
    refreshGameState(teamId).catch((error) => {
      setActionMessage(error.message || 'Unable to reach the local game API');
      setSyncStatus('offline');
    });
  }, [refreshGameState, teamId]);

  const handleSelectTeam = useCallback(async (selectedTeamId) => {
    setSelectingTeam(true);
    setActionMessage('');
    try {
      await requestJson('/game/select-team', {
        method: 'POST',
        body: JSON.stringify({ team_id: selectedTeamId }),
      });
      await refreshGameState(selectedTeamId);
    } catch (error) {
      setActionMessage(error.message || 'Unable to select that franchise');
    } finally {
      setSelectingTeam(false);
    }
  }, [refreshGameState]);

  const handleAdvanceDay = useCallback(async () => {
    if (advancing) return;
    setAdvancing(true);
    setActionMessage('');
    try {
      const response = await fetch(`${API_BASE_URL}/advance-day`, { method: 'POST' });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || 'Unable to advance the calendar');
      const userGame = payload.games.find((playedGame) => playedGame.home_team_id === teamId || playedGame.away_team_id === teamId);
      setActionMessage(
        userGame
          ? `Day ${payload.calendar.current_day}: ${userGame.away_team} ${userGame.away_score} · ${userGame.home_team} ${userGame.home_score}${userGame.overtime ? ' (OT)' : ''}`
          : `Day ${payload.calendar.current_day}: no game for ${teamState.name}`,
      );
      await refreshGameState(teamId);
    } catch (error) {
      setActionMessage(error.message || 'Unable to advance the calendar');
    } finally {
      setAdvancing(false);
    }
  }, [advancing, refreshGameState, teamId, teamState.name]);

  const handleResetGame = useCallback(async () => {
    setResetting(true);
    setActionMessage('');
    try {
      await requestJson('/game/reset', {
        method: 'POST',
        body: JSON.stringify({ confirm: 'RESET', seed: 7, save_name: 'Alpha Franchise' }),
      });
      await refreshGameState(1);
      setActionMessage('New eight-team alpha save created.');
      setActiveTab('dashboard');
    } catch (error) {
      setActionMessage(error.message || 'Unable to create a new game');
      setActiveTab('dashboard');
    } finally {
      setResetting(false);
    }
  }, [refreshGameState]);

  const content = useMemo(() => {
    if (activeTab === 'roster') return <RosterScreen roster={roster} teamState={teamState} syncStatus={syncStatus} />;
    if (activeTab === 'games') return <GamesScreen teamId={teamId} schedule={schedule} standings={standings} syncStatus={syncStatus} />;
    if (activeTab === 'trade') return <TradeScreen teamId={teamId || 1} onTradeComplete={refreshGameState} />;
    if (activeTab === 'office') return <OfficeScreen game={game} onResetGame={handleResetGame} resetting={resetting} />;
    return <DashboardScreen game={game} teamId={teamId} teamState={teamState} syncStatus={syncStatus} onAdvanceDay={handleAdvanceDay} advancing={advancing} actionMessage={actionMessage} onSelectTeam={handleSelectTeam} selectingTeam={selectingTeam} onNavigate={setActiveTab} onRetry={handleRetry} />;
  }, [actionMessage, activeTab, advancing, game, handleAdvanceDay, handleResetGame, handleRetry, handleSelectTeam, refreshGameState, resetting, roster, schedule, selectingTeam, standings, syncStatus, teamId, teamState]);

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
  warningBanner: { color: COLORS.yellow, backgroundColor: '#3a2a08', borderColor: '#7a5c13', borderWidth: 1, borderRadius: 8, padding: 10, fontSize: 12, lineHeight: 18, marginBottom: 10 },
  selectorWrap: { marginBottom: 10 },
  selectorRow: { paddingVertical: 7, paddingRight: 10 },
  teamChip: { backgroundColor: COLORS.card, borderColor: COLORS.line, borderWidth: 1, borderRadius: 99, paddingVertical: 8, paddingHorizontal: 12, marginRight: 7 },
  teamChipActive: { backgroundColor: COLORS.blueSoft, borderColor: COLORS.blue },
  teamChipText: { color: COLORS.muted, fontSize: 11, fontWeight: '800' },
  teamChipTextActive: { color: COLORS.text },
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
  rosterTabButton: { flex: 1, borderRadius: 8, alignItems: 'center' },
  rosterTab: { color: COLORS.muted, paddingVertical: 10, fontSize: 11, fontWeight: '800' },
  rosterTabActive: { backgroundColor: COLORS.blueSoft },
  rosterTabTextActive: { color: COLORS.text },
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
  resultRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  resultScore: { fontSize: 23, fontWeight: '900' },
  standingsHeader: { flexDirection: 'row', paddingVertical: 8, paddingHorizontal: 8, borderBottomColor: COLORS.line, borderBottomWidth: 1 },
  standingsRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10, paddingHorizontal: 8, borderBottomColor: '#102940', borderBottomWidth: 1 },
  standingsRowActive: { backgroundColor: COLORS.blueSoft, borderRadius: 7 },
  standingCell: { color: COLORS.muted, fontSize: 10, fontWeight: '900', flex: 0.55, textAlign: 'center' },
  standingCellValue: { color: COLORS.text, fontSize: 12, flex: 0.55, textAlign: 'center' },
  standingPoints: { color: COLORS.green, fontWeight: '900' },
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
  tradeHistoryText: { flex: 1, paddingRight: 8 },
  tradeHistoryStatus: { fontSize: 11, fontWeight: '900' },
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
  comingSoon: { color: COLORS.yellow, fontSize: 9, fontWeight: '900', width: 76, textAlign: 'right' },
  resetButton: { backgroundColor: '#5f2229', borderColor: COLORS.red, borderWidth: 1, borderRadius: 9, paddingVertical: 13, alignItems: 'center', marginTop: 14 },
  resetButtonArmed: { backgroundColor: '#9b1c29' },
  resetWarning: { color: COLORS.red, fontSize: 11, lineHeight: 16, marginTop: 8, textAlign: 'center' },
  officeArrow: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#0c642b', alignItems: 'center', justifyContent: 'center' },
  officeArrowText: { color: COLORS.green, fontSize: 22, fontWeight: '900', marginTop: -2 },
  bottomNav: { height: 72, backgroundColor: '#07121f', borderTopWidth: 1, borderTopColor: COLORS.line, flexDirection: 'row', paddingBottom: 6 },
  navItem: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  navIcon: { color: COLORS.muted, fontSize: 21 },
  navIconActive: { color: COLORS.blue },
  navLabel: { color: COLORS.muted, fontSize: 9, fontWeight: '900', marginTop: 4 },
  navLabelActive: { color: COLORS.blue },
});
