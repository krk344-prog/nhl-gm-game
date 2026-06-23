import os
import sys
import math
import sqlite3
import random

# ==============================================================================
# 1. ARCHITECTURE BASELINE: PERSISTENT DATABASE SYSTEM INITIALIZER
# ==============================================================================
def init_database():
    """Establishes transaction-isolated SQLite anchor and populates complete rosters."""
    conn = sqlite3.connect("nhl_gm_core.db", isolation_level="EXCLUSIVE")
    cursor = conn.cursor()
    
    # Core Chronological Matrix & Asset Tracking Accrual Hub
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_calendar (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_day INTEGER DEFAULT 1,
            max_days INTEGER DEFAULT 186,
            salary_cap_ceiling REAL DEFAULT 92000000.0,
            accrued_margin REAL DEFAULT 0.0
        )
    """)
    
    # Corporate Franchise Data Hub
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            city TEXT,
            tier TEXT, -- 'NHL', 'AHL'
            cash_balance REAL DEFAULT 25000000.0,
            gm_trust_score REAL DEFAULT 70.0,
            franchise_mandate TEXT DEFAULT 'Moneyball Auditor', -- 'Win-Now Titan', 'Moneyball Auditor'
            relationship_score REAL DEFAULT 50.0 -- User relational tax tracker (R_ij)
        )
    """)
    
    # Comprehensive Micro-Skill Coordinates Matrix [30, 99]
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            name TEXT,
            age INTEGER,
            position TEXT, -- 'F', 'D', 'G'
            archetype TEXT,
            shooting INTEGER CHECK(shooting BETWEEN 30 AND 99),
            passing INTEGER CHECK(passing BETWEEN 30 AND 99),
            positioning INTEGER CHECK(positioning BETWEEN 30 AND 99),
            reflexes INTEGER CHECK(reflexes BETWEEN 30 AND 99),
            speed INTEGER CHECK(speed BETWEEN 30 AND 99),
            checking INTEGER CHECK(checking BETWEEN 30 AND 99),
            aav REAL,
            contract_years INTEGER,
            fatigue REAL DEFAULT 0.0,
            back_to_back_started INTEGER DEFAULT 0,
            scout_observations INTEGER DEFAULT 0,
            FOREIGN KEY(team_id) REFERENCES teams(id)
        )
    """)
    
    # Check if database require fresh asset generation seeding
    cursor.execute("SELECT COUNT(*) FROM league_calendar")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO league_calendar (current_day, accrued_margin) VALUES (1, 0.0)")
        
        # Seed 1-to-1 Corporate Organizational Franchises
        cursor.execute("INSERT INTO teams (name, city, tier, franchise_mandate, relationship_score) VALUES ('Titans', 'New York', 'NHL', 'Win-Now Titan', 75.0)")
        cursor.execute("INSERT INTO teams (name, city, tier, franchise_mandate, relationship_score) VALUES ('Auditors', 'Detroit', 'NHL', 'Moneyball Auditor', 45.0)")
        cursor.execute("INSERT INTO teams (name, city, tier, franchise_mandate, relationship_score) VALUES ('Farmhorns', 'Grand Rapids', 'AHL', 'Moneyball Auditor', 100.0)")
        
        # Generation Arrays for System Seeding
        first_names = ["Connor", "Auston", "Nikita", "Nathan", "Leon", "Cale", "Igor", "Andrei", "Artemi", "Sidney", "David", "Mitchell", "Rasmus", "Aleksander", "Matthew", "Quinn"]
        last_names = ["McHockey", "Matthews", "Kucherov", "MacKinnon", "Draisaitl", "Makar", "Shesterkin", "Vasilevskiy", "Panarin", "Crosby", "Pastrnak", "Marner", "Dahlin", "Barkov", "Tkachuk", "Hughes"]
        
        # Generate Complete 23-Man Rosters for Main NHL Competitors to keep compliance legal
        for team_idx in [1, 2]:
            # Forwards Seeding (13 Forwards per team)
            for f in range(13):
                p_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                arch = random.choice(["Elite Playmaker", "Volume Sniper", "Two-Way Forward"])
                shoot = random.randint(85, 98) if arch == "Volume Sniper" else random.randint(60, 85)
                pass_val = random.randint(86, 99) if arch == "Elite Playmaker" else random.randint(60, 85)
                cursor.execute("INSERT INTO players (team_id, name, age, position, archetype, shooting, passing, positioning, reflexes, speed, checking, aav, contract_years) VALUES (?, ?, ?, 'F', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (team_idx, p_name, random.randint(19, 35), arch, shoot, pass_val, random.randint(65, 90), random.randint(30, 50), random.randint(75, 95), random.randint(60, 90), random.randint(4500000, 11000000), random.randint(1, 7)))
            
            # Defensemen Seeding (8 Defensemen per team)
            for d in range(8):
                p_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                arch = random.choice(["Offensive D-Man", "Defensive D-Man"])
                pos_val = random.randint(85, 98) if arch == "Defensive D-Man" else random.randint(65, 84)
                chk_val = random.randint(82, 99) if arch == "Defensive D-Man" else random.randint(60, 80)
                cursor.execute("INSERT INTO players (team_id, name, age, position, archetype, shooting, passing, positioning, reflexes, speed, checking, aav, contract_years) VALUES (?, ?, ?, 'D', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (team_idx, p_name, random.randint(20, 36), arch, random.randint(50, 75), random.randint(75, 92), pos_val, random.randint(30, 50), random.randint(70, 92), chk_val, random.randint(3500000, 8500000), random.randint(1, 6)))
            
            # Goaltenders Seeding (2 Goaltenders per team)
            for g in range(2):
                p_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                arch = random.choice(["Butterfly Goalie", "Hybrid Goalie"])
                cursor.execute("INSERT INTO players (team_id, name, age, position, archetype, shooting, passing, positioning, reflexes, speed, checking, aav, contract_years) VALUES (?, ?, ?, 'G', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               (team_idx, p_name, random.randint(22, 34), arch, random.randint(30, 45), random.randint(50, 75), random.randint(85, 98), random.randint(86, 99), random.randint(65, 88), random.randint(30, 40), random.randint(2000000, 7500000), random.randint(1, 5)))
                
        # Seed AHL Minor Affiliate Reserves Group (Farmhorns)
        for a in range(10):
            p_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            cursor.execute("INSERT INTO players (team_id, name, age, position, archetype, shooting, passing, positioning, reflexes, speed, checking, aav, contract_years) VALUES (3, ?, ?, 'F', 'Minor Prospect', 55, 55, 55, 30, 68, 60, 775000, 2)",
                           (p_name, random.randint(18, 24)))
            
    conn.commit()
    conn.close()

# ==============================================================================
# 2. CORE ENGINES MODULE: CBA COMPLIANCE, FINANCIALS, & SCATTER MATRIX
# ==============================================================================
class ComplianceGate:
    """Enforces absolute legal fences around multi-tiered franchise roster sheets."""
    @staticmethod
    def verify_roster_legality(team_id):
        conn = sqlite3.connect("nhl_gm_core.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(aav) FROM players WHERE team_id = ?", (team_id,))
        count, total_aav = cursor.fetchone()
        total_aav = total_aav if total_aav else 0.0
        
        cursor.execute("SELECT salary_cap_ceiling FROM league_calendar WHERE id = 1")
        cap_ceiling = cursor.fetchone()[0]
        conn.close()
        
        errors = []
        if count > 23:
            errors.append(f"Roster Size Override Tax: {count}/23 Players active.")
        if total_aav > cap_ceiling:
            errors.append(f"CBA Cap Ceiling Breached: ${total_aav:,.2f} / ${cap_ceiling:,.2f}")
            
        return len(errors) == 0, errors

class ScoutingFogEngine:
    """Applies analytical attribute masking using exponential observation curves."""
    @staticmethod
    def calculate_current_sigma(observations, efficiency=1.0, base_sigma=20.0, lambda_constant=0.35):
        # Math formula: sigma_current = sigma_base * e^(-lambda * N_obs * eff)
        return base_sigma * math.exp(-(lambda_constant * observations * efficiency))

    @staticmethod
    def get_masked_display(base_value, observations):
        sigma = ScoutingFogEngine.calculate_current_sigma(observations)
        if sigma <= 0.75:
            return f"{base_value:<3} [Verified]"
        error_margin = int(round(sigma))
        return f"{base_value:^3} (±{error_margin:<2})"

class DynamicFinancialPool:
    """Calculates chronological daily roster tracking fee matrices."""
    @staticmethod
    def process_daily_cap_accrual():
        conn = sqlite3.connect("nhl_gm_core.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT current_day, max_days, salary_cap_ceiling FROM league_calendar WHERE id = 1")
        cal = cursor.fetchone()
        
        # Fetch active operational rosters
        cursor.execute("SELECT id, tier FROM teams")
        teams = cursor.fetchall()
        
        for team in teams:
            cursor.execute("SELECT SUM(aav) as total_aav FROM players WHERE team_id = ?", (team['id'],))
            r_sum = cursor.fetchone()['total_aav']
            r_sum = r_sum if r_sum else 0.0
            
            # Daily rate formula tracking charge parameters
            daily_charge = r_sum / float(cal['max_days'])
            
            # Deduct running operations balance sheet
            cursor.execute("UPDATE teams SET cash_balance = cash_balance - ? WHERE id = ?", (daily_charge, team['id']))
            
            # If tracking user team (ID=1), store accrued deadline capital pool
            if team['id'] == 1:
                daily_max = cal['salary_cap_ceiling'] / float(cal['max_days'])
                daily_margin = daily_max - daily_charge
                cursor.execute("UPDATE league_calendar SET accrued_margin = accrued_margin + ? WHERE id = 1", (daily_margin,))
                
        conn.commit()
        conn.close()

# ==============================================================================
# 3. TACTICAL GAMEPLAY FRAMEWORK: SHIFT SIMULATION ENGINE
# ==============================================================================
class TacticalMatchSimulator:
    """Resolves micro-attribute coordinate frameworks via deep 60-minute shift sequences."""
    def __init__(self, home_team_id, away_team_id):
        self.home_id = home_team_id
        self.away_id = away_team_id
        
    def gather_roster_dictionary(self, team_id):
        conn = sqlite3.connect("nhl_gm_core.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, position, archetype, shooting, passing, positioning, reflexes, speed, checking, fatigue, back_to_back_started FROM players WHERE team_id = ?", (team_id,))
        rows = cursor.fetchall()
        conn.close()
        
        roster = {'F': [], 'D': [], 'G': []}
        for r in rows:
            p = dict(r)
            # Apply Goalie consecutive-night rest override performance tax overrides
            if p['position'] == 'G' and p['back_to_back_started'] == 1:
                p['positioning'] = max(30, int(p['positioning'] * 0.95))
                p['reflexes'] = max(30, int(p['reflexes'] * 0.95))
            roster[p['position']].append(p)
        return roster

    def execute_match_simulation(self):
        h_roster = self.gather_roster_dictionary(self.home_id)
        a_roster = self.gather_roster_dictionary(self.away_id)
        
        # Verify line configurations are loaded correctly before entry
        if not h_roster['G'] or not a_roster['G'] or len(h_roster['F']) < 3 or len(a_roster['F']) < 3:
            return "Execution Halted: Operational roster depth criteria error."

        h_goals, a_goals = 0, 0
        h_corsi, a_corsi = 0, 0
        match_log = []
        
        # Run three structural periods comprising 20 simulation ticks each
        for period in range(1, 4):
            match_log.append(f"┌────────────────────────────────────────────────────────┐")
            match_log.append(f"│                  STARTING PERIOD {period:01d}/3                    │")
            match_log.append(f"└────────────────────────────────────────────────────────┘")
            
            for ticks in range(1, 21):
                # Core Shift Selection Variables
                h_f = random.sample(h_roster['F'], 3)
                h_d = random.sample(h_roster['D'], 2) if len(h_roster['D']) >= 2 else h_roster['D']
                a_f = random.sample(a_roster['F'], 3)
                a_d = random.sample(a_roster['D'], 2) if len(a_roster['D']) >= 2 else a_roster['D']
                
                h_g, a_g = h_roster['G'][0], a_roster['G'][0]
                
                # Check for Forward Line Chemistry Handshakes
                h_archs = [p['archetype'] for p in h_f]
                a_archs = [p['archetype'] for p in a_f]
                h_chem = 1.15 if ("Elite Playmaker" in h_archs and "Volume Sniper" in h_archs) else 1.0
                a_chem = 1.15 if ("Elite Playmaker" in a_archs and "Volume Sniper" in a_archs) else 1.0
                
                # Calculate collective team possession metrics (Corsi Generation Loops)
                h_possession = sum(p['speed'] for p in h_f) * h_chem
                a_possession = sum(p['speed'] for p in a_f) * a_chem
                
                if random.random() * (h_possession + a_possession) > a_possession:
                    # Home Team Possession Infiltration Sequence
                    h_corsi += 1
                    shooter = random.choice(h_f)
                    passer = random.choice([p for p in h_f if p != shooter])
                    
                    xG = (shooter['shooting'] / 100.0) * 0.15
                    # Royal Road Cross-Crease Pass Sequence Logic Checks
                    if passer['passing'] > 85:
                        xG *= 1.45
                        rr_flag = "[ROYAL ROAD SEQUENCE]"
                    else:
                        rr_flag = "[PERIMETER VOLLEY]"
                        
                    # Target Goalie Save Selection metrics lookup
                    save_index = (a_g['reflexes'] + a_g['positioning']) / 200.0
                    # Calculate Rebound Realization Value (RRV)
                    rrv = random.random()
                    
                    if rrv > save_index:
                        # Goal converted
                        if random.random() * (xG + (1.0 - save_index)) > (1.0 - save_index):
                            h_goals += 1
                            match_log.append(f"  ⚡ [{ticks:02d}:00] GOAL (HOME) - {shooter['name']} via {passer['name']} {rr_flag}")
                else:
                    # Away Team Possession Infiltration Sequence
                    a_corsi += 1
                    shooter = random.choice(a_f)
                    passer = random.choice([p for p in a_f if p != shooter])
                    
                    xG = (shooter['shooting'] / 100.0) * 0.15
                    if passer['passing'] > 85:
                        xG *= 1.45
                        rr_flag = "[ROYAL ROAD SEQUENCE]"
                    else:
                        rr_flag = "[PERIMETER VOLLEY]"
                        
                    save_index = (h_g['reflexes'] + h_g['positioning']) / 200.0
                    rrv = random.random()
                    
                    if rrv > save_index:
                        if random.random() * (xG + (1.0 - save_index)) > (1.0 - save_index):
                            a_goals += 1
                            match_log.append(f"  ⚡ [{ticks:02d}:00] GOAL (AWAY) - {shooter['name']} via {passer['name']} {rr_flag}")
                            
        # Apply physical performance fatigue and back-to-back night tracking states
        conn = sqlite3.connect("nhl_gm_core.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE players SET fatigue = fatigue + 25.0, back_to_back_started = 1 WHERE id = ?", (h_roster['G'][0]['id'],))
        cursor.execute("UPDATE players SET fatigue = fatigue + 25.0, back_to_back_started = 1 WHERE id = ?", (a_roster['G'][0]['id'],))
        conn.commit()
        conn.close()
        
        match_log.append("═" * 56)
        match_log.append(f"  FINAL SCORE RESOLVED: HOME {h_goals} - AWAY {a_goals}")
        match_log.append(f"  CORSI EQUIVALENTS METRIC: HOME SHOTS: {h_corsi} | AWAY SHOTS: {a_corsi}")
        match_log.append("═" * 56)
        return "\n".join(match_log)

# ==============================================================================
# 4. EXECUTIVE ANALYTICAL SYSTEMS: CASV TRADE DESK & ARSE RISK CORE
# ==============================================================================
class ContractAdjustedSurplusValueDesk:
    """Evaluates asset trade values matching player capabilities to Franchise Mandates."""
    @staticmethod
    def calculate_player_baseline_asset_value(player_dict):
        # Baseline metric: Mean score across major structural coordinates
        skill_sum = (player_dict['shooting'] + player_dict['passing'] + 
                     player_dict['positioning'] + player_dict['reflexes'] + 
                     player_dict['speed'] + player_dict['checking'])
        base_val = skill_sum / 6.0
        
        # Age-Attrition Drop Scaling Vector Curve
        if player_dict['age'] > 30:
            base_val -= (player_dict['age'] - 30) * 2.5
        elif player_dict['age'] < 23:
            base_val += (23 - player_dict['age']) * 1.5
        return max(10.0, base_val)

    @staticmethod
    def evaluate_casv_index(player_dict, mandate):
        base_val = ContractAdjustedSurplusValueDesk.calculate_player_baseline_asset_value(player_dict)
        cap_weight_scalar = player_dict['aav'] / 1000000.0
        
        # Modify structural focus weighting to follow active Franchise Mandates
        if mandate == 'Moneyball Auditor':
            casv = base_val - (cap_weight_scalar * 4.5)
        else: # Win-Now Titan
            casv = (base_val * 1.35) - (cap_weight_scalar * 2.0)
            
        return casv

    @staticmethod
    def process_trade_proposal(user_player_id, target_team_id, target_player_id):
        conn = sqlite3.connect("nhl_gm_core.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Pull player metrics data records
        cursor.execute("SELECT * FROM players WHERE id = ?", (user_player_id,))
        u_p = dict(cursor.fetchone())
        cursor.execute("SELECT * FROM players WHERE id = ?", (target_player_id,))
        t_p = dict(cursor.fetchone())
        
        # Pull rival general manager tracking parameters
        cursor.execute("SELECT * FROM teams WHERE id = ?", (target_team_id,))
        rival_team = dict(cursor.fetchone())
        conn.close()
        
        # Calculate matching validation metrics
        u_casv = ContractAdjustedSurplusValueDesk.evaluate_casv_index(u_p, rival_team['franchise_mandate'])
        t_casv = ContractAdjustedSurplusValueDesk.evaluate_casv_index(t_p, rival_team['franchise_mandate'])
        
        # Apply the Relational Friction Modifier (R_ij) luxury premium tax
        r_ij = rival_team['relationship_score']
        required_premium_scalar = 1.0 + ((100.0 - r_ij) / 200.0)
        adjusted_threshold_barrier = t_casv * required_premium_scalar
        
        log = []
        log.append(f"Incoming Trade Desk Pitch Analysis Grid:")
        log.append(f"  User Asset: {u_p['name']} | Calculated Valuation Value: {u_casv:.2f}")
        log.append(f"  Rival Asset: {t_p['name']} | Target Base Value Index: {t_casv:.2f}")
        log.append(f"  Rival Alignment Mandate Mode: {rival_team['franchise_mandate']}")
        log.append(f"  Relational Tax Premium Multiplier (R_ij Score {r_ij:.1f}): x{required_premium_scalar:.2f}")
        log.append(f"  Adjusted Barrier Goal Threshold Required: {adjusted_threshold_barrier:.2f}")
        
        # Check transaction gate validation criteria outcomes
        if u_casv >= adjusted_threshold_barrier:
            # Check systemic transaction compliance gate limits
            conn = sqlite3.connect("nhl_gm_core.db")
            cursor = conn.cursor()
            
            # Execute transactional row migrations
            cursor.execute("UPDATE players SET team_id = ? WHERE id = ?", (target_team_id, user_player_id))
            cursor.execute("UPDATE players SET team_id = 1 WHERE id = ?", (target_player_id))
            
            # Check legality states across modified sheets
            h_legal, _ = ComplianceGate.verify_roster_legality(1)
            a_legal, _ = ComplianceGate.verify_roster_legality(target_team_id)
            
            if h_legal and a_legal:
                conn.commit()
                log.append("\n[TRANSACTION APPROVED] Front-office analytics accepted. Trade processed.")
            else:
                conn.rollback()
                log.append("\n[TRADE TRANSACTION BLOCKED] Blocked due to upcoming mid-season salary cap non-compliance.")
            conn.close()
        else:
            log.append("\n[TRADE PROPOSAL REJECTED] Rival engine analysis reports low CASV margin return value.")
            
        return "\n".join(log)

class AdvisorRiskScoringEngine:
    """Computes administrative multi-variable corporate system risk coordinates."""
    @staticmethod
    def generate_executive_analysis_report():
        conn = sqlite3.connect("nhl_gm_core.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM players WHERE team_id = 1")
        roster = cursor.fetchall()
        
        cursor.execute("SELECT * FROM teams WHERE id != 1")
        rivals = cursor.fetchall()
        
        cursor.execute("SELECT * FROM league_calendar WHERE id = 1")
        cal = cursor.fetchone()
        conn.close()
        
        total_aav = sum(p['aav'] for p in roster)
        cap_headroom = cal['salary_cap_ceiling'] - total_aav
        
        # Calculate core cap spending structural leakage metrics
        overpaid_count = 0
        for p in roster:
            p_dict = dict(p)
            base_skill_worth = ContractAdjustedSurplusValueDesk.calculate_player_baseline_asset_value(p_dict)
            if p_dict['aav'] > 5000000 and base_skill_worth < 65.0:
                overpaid_count += 1
                
        # Calculate relational score tracking risk vectors
        mean_r_ij = sum(r['relationship_score'] for r in rivals) / float(len(rivals))
        
        # Core Formula Resolution Grid
        risk_score = 0.0
        risk_score += max(0.0, (total_aav / cal['salary_cap_ceiling']) * 40.0)
        risk_score += (overpaid_count * 12.0)
        risk_score += max(0.0, (100.0 - mean_r_ij) * 0.3)
        risk_score = min(100.0, risk_score)
        
        report = []
        report.append("┌────────────────────────────────────────────────────────┐")
        report.append(f"│         ADVISOR RISK SCORE CALCULATOR MODULE (ARSE)    │")
        report.append(f"│         AGGREGATE RISK EVALUATION CAP INDEX: {risk_score:04.1f}/100 │")
        report.append("└────────────────────────────────────────────────────────┘")
        report.append(f" Operational Vitals Risk Trace Breakdown Summary:")
        report.append(f"  - Active Roster Spending Capacity: ${total_aav:,.2f} / Headroom: ${cap_headroom:,.2f}")
        report.append(f"  - Misaligned Roster Assets Tracked (Low Skill-to-AAV Ratio): {overpaid_count} Skeletons")
        report.append(f"  - System Relational Friction Coefficient (Mean R_ij Hub): {mean_r_ij:.1f}")
        
        if risk_score > 75.0:
            report.append("  [CRITICAL ALERT] Franchise is exposed to financial inflexibility and market locking.")
        elif risk_score > 45.0:
            report.append("  [MODERATE WARNING] Minor asset restructuring required before the upcoming Trade Deadline.")
        else:
            report.append("  [STABLE CONFIGURATION] Roster efficiency curves track within absolute optimal ranges.")
            
        return "\n".join(report)

# ==============================================================================
# 5. USER INTERFACE ARCHITECTURE: GRAPHICAL LEVEL 1 & 2 TERMINAL CONTROLLER
# ==============================================================================
class ExecutiveTerminalApp:
    """Manages dense box-drawing layouts and command-line execution sequences."""
    def __init__(self):
        init_database()

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render_dashboard_header(self):
        conn = sqlite3.connect("nhl_gm_core.db")
        cursor = conn.cursor()
        cursor.execute("SELECT current_day, salary_cap_ceiling, accrued_margin FROM league_calendar WHERE id = 1")
        day, ceiling, margin = cursor.fetchone()
        
        # Calculate Trade Deadline Buying Capacity Equivalents
        days_remaining = max(1, 186 - day)
        buying_power = margin * (186.0 / float(days_remaining))
        
        cursor.execute("SELECT cash_balance, gm_trust_score FROM teams WHERE id = 1")
        cash, trust = cursor.fetchone()
        conn.close()
        
        print("┌──────────────────────────────────────────────────────────────────────────────┐")
        print("│                         NHL FRANCHISE GOVERNANCE RADAR                       │")
        print(f"│ SYSTEM TIMELINE: DAY {day:03d}/186 | OPERATIONAL CASH LEDGER: ${cash:,.2f}       │")
        print(f"│ LEGAL CEILING: ${ceiling:,.2f} | TRADE DEADLINE ACCRUED BUYING POWER: ${buying_power:,.2f}│")
        print(f"│ EXECUTIVE JOB SECURITY INDICATOR INDEX: [{trust:04.1f}/100]                               │")
        print("└──────────────────────────────────────────────────────────────────────────────┐")

    def display_roster_board(self):
        self.clear()
        self.render_dashboard_header()
        print("\n  ## ACTIVE ROSTER AUDIT REGISTRY PANEL (FOG-OF-WAR SIMULATION ENABLED) ##\n")
        
        conn = sqlite3.connect("nhl_gm_core.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, t.name as team_name FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE t.tier = 'NHL' ORDER BY t.id, p.position, p.id
        """)
        players = cursor.fetchall()
        conn.close()
        
        print(f" {'ID':<3} | {'PLAYER NAME':<18} | {'POS':<3} | {'AGE':<3} | {'SHOOTING':<14} | {'PASSING':<14} | {'AAV':<12}")
        print(" ─────────────────────────────────────────────────────────────────────────────")
        for p in players:
            p_dict = dict(p)
            s_mask = ScoutingFogEngine.get_masked_display(p_dict['shooting'], p_dict['scout_observations'])
            p_mask = ScoutingFogEngine.get_masked_display(p_dict['passing'], p_dict['scout_observations'])
            print(f" {p_dict['id']:<3} | {p_dict['name']:<18} | {p_dict['position']:<3} | {p_dict['age']:<3} | {s_mask:<14} | {p_mask:<14} | ${p_dict['aav']:,.0f}")
        
        input("\n Press Enter to cycle tracking frames backward back to terminal center...")

    def execute_scouting_run(self):
        self.clear()
        self.render_dashboard_header()
        print("\n  ## DISPATCHING SCOUTING ASSETS INTO FIELDS ##\n")
        print(" Scanning player attribute vectors and generating direct observation frames...")
        
        conn = sqlite3.connect("nhl_gm_core.db")
        cursor = conn.cursor()
        # Increment observation logs to collapse tracking error standard deviation margins
        cursor.execute("UPDATE players SET scout_observations = scout_observations + 1")
        conn.commit()
        conn.close()
        
        print("\n [SUCCESS] Observation processing loop completed. Uncertainty values condensed.")
        input(" Press Enter to return back to central office dashboard...")

    def deploy_trade_desk(self):
        self.clear()
        self.render_dashboard_header()
        print("\n  ## CONTRACT-ADJUSTED SURPLUS VALUE TRANSACTION HUB (CASV) ##\n")
        
        user_p = input(" Enter the ID code of your Asset to package out: ").strip()
        rival_team = input(" Enter Target Team ID Destination code (2 for Auditors): ").strip()
        rival_p = input(" Enter ID code of target Rival Asset to acquire: ").strip()
        
        if not user_p or not rival_team or not rival_p:
            print(" Error: Input vectors data entry failure.")
            input(" Press Enter to escape trade desk loop...")
            return
            
        self.clear()
        self.render_dashboard_header()
        print("\n Evaluating financial trade matrices across networks...\n")
        
        try:
            trade_result = ContractAdjustedSurplusValueDesk.process_trade_proposal(int(user_p), int(rival_team), int(rival_p))
            print(trade_result)
        except Exception as e:
            print(f" Transaction Blockage Exception: {e}")
            
        input("\n Press Enter to safely disconnect from trade terminal desk pipeline...")

    def deploy_advisor_desk(self):
        self.clear()
        self.render_dashboard_header()
        print("\n Run corporate risk matrix audits...\n")
        report = AdvisorRiskScoringEngine.generate_executive_analysis_report()
        print(report)
        input("\n Press Enter to route back to system navigation matrix...")

    def deploy_tactical_match_arena(self):
        self.clear()
        self.render_dashboard_header()
        print("\n  ## LIVE 60-MINUTE TACTICAL MATCH CALCULATOR ARENA ##\n")
        print(" Loading parameters... Matching up [1] NY Titans vs [2] Detroit Auditors...")
        input(" Roster metrics synchronized. Press Enter to drop puck and run calculation frame...")
        
        self.clear()
        sim = TacticalMatchSimulator(1, 2)
        log = sim.execute_match_simulation()
        print(log)
        input("\n Simulation frames stored. Press Enter to unlock console back to home dashboard...")

    def advance_simulation_time(self):
        self.clear()
        self.render_dashboard_header()
        print("\n  ## INCREMENTING TEMPORAL LEAGUE CALENDAR INDEX CORRIDOR (+24H) ##\n")
        
        conn = sqlite3.connect("nhl_gm_core.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE league_calendar SET current_day = current_day + 1 WHERE id = 1")
        # Apply physical system recovery decay curves
        cursor.execute("UPDATE players SET fatigue = MAX(0.0, fatigue - 5.0)")
        cursor.execute("UPDATE players SET back_to_back_started = 0 WHERE fatigue == 0.0")
        conn.commit()
        conn.close()
        
        # Fire structural fiscal tracking deductions
        DynamicFinancialPool.process_daily_cap_accrual()
        
        print(" [CHRONO TICK] Daily financial balance sheets settled.")
        print(" Cash asset reserves recalculated matching daily player roster charge fields.")
        input("\n Press Enter to execute dashboard configuration reload sequences...")

    def run_main_loop(self):
        while True:
            self.clear()
            self.render_dashboard_header()
            print("\n   [1] Audit Full League Rosters (Review Fog-of-War Attributes)")
            print("   [2] Deploy Scouting Corps (Pierce Skill Uncertainty Margin)")
            print("   [3] Propose Roster Trade Package (CASV Transaction Evaluator)")
            print("   [4] Consult AI Front-Office Advisor Desk (ARSE Metrics Index)")
            print("   [5] Launch 60-Minute Tactical Shift Match Simulation Core")
            print("   [6] Advance Calendar Timeline Matrix (+24 Hours Operations Charge)")
            print("   [7] Exit Subsystems Control Center")
            
            choice = input("\n Select Action Vector Grid [1-7]: ").strip()
            if choice == "1":
                self.display_roster_board()
            elif choice == "2":
                self.execute_scouting_run()
            elif choice == "3":
                self.deploy_trade_desk()
            elif choice == "4":
                self.deploy_advisor_desk()
            elif choice == "5":
                self.deploy_tactical_match_arena()
            elif choice == "6":
                self.advance_simulation_time()
            elif choice == "7":
                print("\n Shutting down active administrative pipelines securely. Data states persistent.")
                sys.exit(0)

# ==============================================================================
# 6. APPLICATION BOOT ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app = ExecutiveTerminalApp()
    app.run_main_loop()
