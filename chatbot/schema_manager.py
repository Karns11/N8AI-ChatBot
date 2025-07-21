import yaml
import os
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


class SchemaManager:
    """Manages database schema information from YAML files."""
    
    def __init__(self, schema_file_path: Optional[str] = None):
        """
        Initialize SchemaManager with optional custom schema file path.
        
        Args:
            schema_file_path: Path to YAML schema file. If None, uses default location.
        """
        if schema_file_path:
            self.schema_file_path = Path(schema_file_path)
        else:
            # Default to schema.yaml in the project root
            try:
                from django.conf import settings
                self.schema_file_path = Path(settings.BASE_DIR) / 'schema.yaml'
            except (ImportError, RuntimeError):
                # Fallback for non-Django environments
                self.schema_file_path = Path.cwd() / 'schema.yaml'
        
        self._schema_cache = None
        self._last_modified = None
    
    def load_schema_from_yaml(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load schema information from YAML file.
        
        Expected YAML format:
        # Data Warehouse Schema Configuration
        # This file defines the structure of your data warehouse tables
        # Update this file to reflect your actual database schema

        tables:
        - name: warehouse.dim_date
            description: >
            The date dimension table used for time-based filtering, grouping, and reporting.
            Includes calendar, fiscal, and derived fields to simplify date-related analysis.

            columns:
            - name: as_of_date
                description: "Full calendar date. This is the main date value for filtering."
            - name: date_id
                description: "Numeric unique identifier for the date, formatted as YYYYMMDD."
            - name: day
                description: "Day of the month (1 to 31)."
            - name: day_suffix
                description: "Day suffix for display purposes, such as 'st', 'nd', 'rd', or 'th'."
            - name: day_name
                description: "Full name of the day, for example 'Monday' or 'Tuesday'."
            - name: weekday_ind
                description: "Indicator showing if the date is a weekday. 1 = Yes, 0 = No."
            - name: weekday_num
                description: "Numeric day of the week, where 1 = Monday and 7 = Sunday."
            - name: week_of_month
                description: "Week number within the month."
            - name: week_of_year
                description: "Week number within the year, starting from 1."
            - name: iso_week
                description: "ISO 8601 week number, standardized week numbering."
            - name: month
                description: "Month number (1 = January, 12 = December)."
            - name: month_name
                description: "Full name of the month, for example 'January'."
            - name: month_abbrev
                description: "Three-letter abbreviation of the month, such as 'Jan' or 'Feb'."
            - name: quarter
                description: "Quarter of the year (1 to 4)."
            - name: quarter_name
                description: "Text label for the quarter, such as 'Q1' or 'Q2'."
            - name: year
                description: "Calendar year in 4-digit format."
            - name: iso_year
                description: "Year based on ISO week date standard."
            - name: year_month
                description: "Combined year and month in YYYY-MM format."
            - name: year_quarter
                description: "Combined year and quarter, for example '2024-Q1'."
            - name: first_day_of_month
                description: "Date of the first day of the month."
            - name: last_day_of_month
                description: "Date of the last day of the month."
            - name: first_day_of_qtr
                description: "Date of the first day of the quarter."
            - name: last_day_of_qtr
                description: "Date of the last day of the quarter."
            - name: first_day_of_year
                description: "Date of the first day of the year."
            - name: last_day_of_year
                description: "Date of the last day of the year."
            - name: day_of_year
                description: "The day number within the year, ranging from 1 to 366."
            - name: is_holiday
                description: "Indicator showing if the date is a recognized holiday. 1 = Yes, 0 = No."
            - name: holiday_name
                description: "Name of the holiday, if applicable."
            - name: fiscal_month
                description: "Month number according to the organization's fiscal calendar."
            - name: fiscal_quarter
                description: "Quarter according to the organization's fiscal calendar."
            - name: fiscal_year
                description: "Year according to the organization's fiscal calendar."
            - name: is_weekend
                description: "Indicator showing if the date falls on a weekend. 1 = Yes, 0 = No."
            - name: is_last_day_of_month
                description: "Indicator showing if the date is the last day of the month."
            - name: is_first_day_of_month
                description: "Indicator showing if the date is the first day of the month."
            - name: prev_day
                description: "Date value for the previous day."
            - name: next_day
                description: "Date value for the next day."
            - name: prev_month
                description: "Same day in the previous month, or adjusted if day does not exist."
            - name: next_month
                description: "Same day in the next month, or adjusted if day does not exist."
            - name: prev_year
                description: "Same day in the previous year, accounting for leap years."
            - name: next_year
                description: "Same day in the next year, accounting for leap years."
            - name: days_in_month
                description: "Total number of days in the current month."
            - name: leap_year
                description: "Indicator showing if the year is a leap year. 1 = Yes, 0 = No."
            - name: iso_day_of_week
                description: "ISO standard day number, where 1 = Monday and 7 = Sunday."
            - name: unix_timestamp
                description: "Unix timestamp representing the start of the date in seconds."
            - name: julian_date
                description: "Julian date number used in scientific and astronomical calculations."
            - name: created_at
                description: "Timestamp for when this record was created in the table."

        - name: warehouse.dim_player
            description: >
            Player dimension table containing biographical, physical, and baseball-related information
            for players appearing in MLB data. Used to enrich fact tables with player details.

            columns:
            - name: player_sk
                description: "Surrogate key for the player, used for joining to fact tables."
            - name: source_id
                description: "Source system identifier for the player, often MLB ID."
            - name: full_name
                description: "Full name of the player."
            - name: first_name
                description: "First name of the player."
            - name: last_name
                description: "Last name of the player."
            - name: player_link
                description: "URL link to the player's official MLB page or profile."
            - name: primary_number
                description: "Player's jersey number."
            - name: birth_date
                description: "Player's date of birth."
            - name: birth_city
                description: "City where the player was born."
            - name: birth_state_province
                description: "State or province where the player was born."
            - name: birth_country
                description: "Country where the player was born."
            - name: height
                description: "Player's height, typically in inches or centimeters."
            - name: weight
                description: "Player's weight, typically in pounds or kilograms."
            - name: is_active
                description: "Indicates if the player is currently active. 1 = Yes, 0 = No."
            - name: draft_year
                description: "Year the player was drafted into MLB."
            - name: mlb_debut_date
                description: "Date of the player's Major League debut."
            - name: strike_zone_top
                description: "Top boundary of the player's strike zone, usually in feet."
            - name: strike_zone_bottom
                description: "Bottom boundary of the player's strike zone, usually in feet."
            - name: primary_position_name
                description: "Full name of the player's primary position, e.g., 'Shortstop'."
            - name: primary_position_type
                description: "General type of position, such as 'Infield' or 'Outfield'."
            - name: primary_position_abbreviation
                description: "Standard abbreviation for the position, such as 'SS' for shortstop."
            - name: bat_side_code
                description: "Player's batting side. 'L' = Left, 'R' = Right, 'S' = Switch hitter."
            - name: pitch_hand_code
                description: "Player's throwing hand. 'L' = Left, 'R' = Right."
            - name: team
                description: "Current MLB team of the player."
            - name: effective_date
                description: "Date when this player record became effective."
            - name: expire_date
                description: "Date when this player record expired or was replaced."
            - name: current_flag
                description: "Indicates if this record is the current version. 1 = Yes, 0 = No."

        - name: warehouse.dim_team
            description: >
            Team dimension table containing team names, locations, league details, and franchise history.
            Used to provide team-specific attributes for baseball reporting and analysis.

            columns:
            - name: team_sk
                description: "Surrogate key for the team, used for joining to fact tables."
            - name: source_id
                description: "Source system identifier for the team, typically from MLB systems."
            - name: team_full_name
                description: "Full name of the team, including city and nickname. Example: 'Los Angeles Angels'."
            - name: team_link
                description: "URL to the team's official MLB page or resource."
            - name: team_code
                description: "Team code used by MLB or other data providers, usually short alphanumeric."
            - name: file_code
                description: "Code used in file systems, URLs, or data feeds to identify the team."
            - name: team_abbreviation
                description: "Three-letter abbreviation for the team, for example 'LAA' for Los Angeles Angels."
            - name: team_name
                description: "Nickname or common name of the team, for example 'Angels'."
            - name: location_name
                description: "City or location where the team is based."
            - name: first_year_of_play
                description: "Year the team first played in the league."
            - name: short_name
                description: "Short version of the team name, often used for display or UI."
            - name: franchise_name
                description: "Full franchise name, which may differ from the current team name due to relocation or rebranding."
            - name: club_name
                description: "Club name or parent organization behind the team."
            - name: is_active
                description: "Indicator showing if the team is currently active in the league. 1 = Yes, 0 = No."
            - name: venue_name
                description: "Name of the team's home stadium or venue."
            - name: league_name
                description: "Name of the league the team belongs to, such as 'American League'. Also includes minor leagues."
            - name: division_name
                description: "Division within the league, for example 'AL West'."
            - name: sport_name
                description: "Sport associated with the team, typically 'Baseball'."
            - name: effective_date
                description: "Date when this team record became effective."
            - name: expire_date
                description: "Date when this record expired or was replaced."
            - name: current_flag
                description: "Indicates if this is the current active record for the team. Y = Yes, N = No."

        - name: warehouse.fact_player_stats
            description: >
            Fact table containing player-level offensive statistics for MLB games and seasons.
            Includes batting performance metrics, derived statistics, and season-level aggregations. THIS CONTAINS ONLY THE ACCUMULATIONS FOR THE MOST RECENT DATE IN THE DATA WAREHOUSE. NO HISTORY IN THIS TABLE.

            columns:
            - name: player_sk
                description: "Surrogate key referencing the player in dim_player."
            - name: team_sk
                description: "Surrogate key referencing the team in dim_team."
            - name: num_g
                description: "Total games played by the player."
            - name: pa
                description: "Total plate appearances by the player."
            - name: ab
                description: "Total official at-bats by the player."
            - name: num_hits
                description: "Total hits by the player, including singles, doubles, triples, and home runs."
            - name: num_singles
                description: "Total singles hit by the player."
            - name: num_doubles
                description: "Total doubles hit by the player."
            - name: num_triples
                description: "Total triples hit by the player."
            - name: num_hr
                description: "Total home runs hit by the player."
            - name: num_rbi
                description: "Total runs batted in (RBIs) by the player."
            - name: num_walks
                description: "Total walks (bases on balls) drawn by the player."
            - name: num_strikeouts
                description: "Total strikeouts by the player."
            - name: batting_avg
                description: "Player's batting average (hits divided by at-bats)."
            - name: obp
                description: "On-base percentage for the player."
            - name: slg
                description: "Slugging percentage for the player, measuring power-hitting."
            - name: ops
                description: "On-base plus slugging (OPS) for the player, combining on-base and slugging."
            - name: total_bases
                description: "Total bases accumulated from hits (singles = 1, doubles = 2, etc.)."
            - name: num_gidp
                description: "Total grounded into double plays by the player."
            - name: num_hbp
                description: "Total times the player was hit by a pitch."
            - name: num_sh
                description: "Total sacrifice hits (bunts) by the player."
            - name: num_sf
                description: "Total sacrifice flies by the player."
            - name: num_ibb
                description: "Total intentional walks issued to the player."
            - name: season
                description: "Season year for which the statistics apply."
            - name: as_of_date
                description: "Date corresponding to the latest update of the statistics. MOST RECENT DATE ONLY. NO HISTORY IN THIS TABLE."
            - name: is_currently_qualified
                description: "Indicator showing if the player is currently qualified for leaderboards. 1 = Yes, 0 = No."

        - name: warehouse.fact_player_stats_history
            description: >
            Historical fact table containing snapshots of player-level offensive statistics for MLB seasons.
            Tracks changes to player stats over time to enable trend analysis and point-in-time reporting. THIS TABLE CONTAINS ALL HISTORY.

            columns:
            - name: player_sk
                description: "Surrogate key referencing the player in dim_player."
            - name: team_sk
                description: "Surrogate key referencing the team in dim_team."
            - name: num_g
                description: "Total games played by the player as of the snapshot date."
            - name: pa
                description: "Total plate appearances by the player as of the snapshot date."
            - name: ab
                description: "Total official at-bats by the player as of the snapshot date."
            - name: num_hits
                description: "Total hits by the player, including singles, doubles, triples, and home runs."
            - name: num_singles
                description: "Total singles hit by the player."
            - name: num_doubles
                description: "Total doubles hit by the player."
            - name: num_triples
                description: "Total triples hit by the player."
            - name: num_hr
                description: "Total home runs hit by the player."
            - name: num_rbi
                description: "Total runs batted in (RBIs) by the player."
            - name: num_walks
                description: "Total walks (bases on balls) drawn by the player."
            - name: num_strikeouts
                description: "Total strikeouts by the player."
            - name: batting_avg
                description: "Player's batting average (hits divided by at-bats) as of the snapshot date."
            - name: obp
                description: "On-base percentage for the player as of the snapshot date."
            - name: slg
                description: "Slugging percentage for the player as of the snapshot date."
            - name: ops
                description: "On-base plus slugging (OPS) for the player as of the snapshot date."
            - name: total_bases
                description: "Total bases accumulated from hits as of the snapshot date."
            - name: num_gidp
                description: "Total grounded into double plays by the player."
            - name: num_hbp
                description: "Total times the player was hit by a pitch."
            - name: num_sh
                description: "Total sacrifice hits (bunts) by the player."
            - name: num_sf
                description: "Total sacrifice flies by the player."
            - name: num_ibb
                description: "Total intentional walks issued to the player."
            - name: season
                description: "Season year for which the statistics apply."
            - name: as_of_date
                description: "Snapshot date representing when these statistics were recorded."
            - name: is_currently_qualified
                description: "Indicator showing if the player was qualified for leaderboards as of the snapshot date. 1 = Yes, 0 = No."

        - name: warehouse.fact_team_games
            description: >
            Fact table containing team-level game counts for MLB seasons.
            Tracks the number of games played by each team, used to support player qualification rules and performance analysis.

            columns:
            - name: team_sk
                description: "Surrogate key referencing the team in dim_team."
            - name: as_of_date
                description: "Snapshot date representing when the games played count was recorded. Should also be used in joins to obtain the number of games a team played when joining to other facts."
            - name: season
                description: "Season year for which the games played count applies."
            - name: gp
                description: "Total number of games played by the team as of the snapshot date."

        - name: fact_team_games_history
            description: >
            Historical fact table containing snapshots of team-level game counts for MLB seasons.
            Tracks the number of games played by each team over time to support player qualification, trend analysis, and historical reporting.

            columns:
            - name: team_sk
                description: "Surrogate key referencing the team in dim_team."
            - name: as_of_date
                description: "Snapshot date representing when the games played count was recorded. Should also be used in joins to obtain the number of games a team played when joining to other facts."
            - name: season
                description: "Season year for which the games played count applies."
            - name: gp
                description: "Total number of games played by the team as of the snapshot date."

        """
        try:
            # Check if file exists
            if not self.schema_file_path.exists():
                logger.warning(f"Schema file not found: {self.schema_file_path}")
                return {}
            
            # Check if file has been modified
            current_modified = self.schema_file_path.stat().st_mtime
            if (self._schema_cache is not None and 
                self._last_modified is not None and 
                current_modified <= self._last_modified):
                return self._schema_cache
            
            # Load and parse YAML
            with open(self.schema_file_path, 'r', encoding='utf-8') as file:
                schema_data = yaml.safe_load(file)
            
            # Transform to expected format
            schema_info = {}
            if 'tables' in schema_data:
                tables = schema_data['tables']
                
                # Handle both list and dict formats
                if isinstance(tables, list):
                    # List format: tables is a list of table objects
                    for table in tables:
                        table_name = table.get('name', '')
                        columns = table.get('columns', [])
                        schema_info[table_name] = []
                        for column in columns:
                            schema_info[table_name].append({
                                'column_name': column.get('name', ''),
                                'data_type': column.get('type', 'varchar(255)'),  # Default type
                                'is_nullable': column.get('nullable', True),
                                'column_default': column.get('default', ''),
                                'description': column.get('description', '')
                            })
                elif isinstance(tables, dict):
                    # Dict format: tables is a dict with table names as keys
                    for table_name, columns in tables.items():
                        schema_info[table_name] = []
                        for column in columns:
                            schema_info[table_name].append({
                                'column_name': column.get('name', ''),
                                'data_type': column.get('type', ''),
                                'is_nullable': column.get('nullable', True),
                                'column_default': column.get('default', ''),
                                'description': column.get('description', '')
                            })
            
            # Update cache
            self._schema_cache = schema_info
            self._last_modified = current_modified
            
            logger.info(f"Schema loaded from {self.schema_file_path}: {len(schema_info)} tables")
            return schema_info
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML schema file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading schema from YAML: {e}")
            return {}
    
    def get_schema_for_prompt(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get schema information formatted for prompt inclusion."""
        return self.load_schema_from_yaml()
    
    def validate_schema_file(self) -> tuple[bool, str]:
        """
        Validate the schema YAML file format.
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            if not self.schema_file_path.exists():
                return False, f"Schema file not found: {self.schema_file_path}"
            
            with open(self.schema_file_path, 'r', encoding='utf-8') as file:
                schema_data = yaml.safe_load(file)
            
            if not isinstance(schema_data, dict):
                return False, "Schema file must contain a dictionary"
            
            if 'tables' not in schema_data:
                return False, "Schema file must contain 'tables' key"
            
            tables = schema_data['tables']
            if not isinstance(tables, (dict, list)):
                return False, "'tables' must be a dictionary or list"
            
            if isinstance(tables, list):
                # List format validation
                for i, table in enumerate(tables):
                    if not isinstance(table, dict):
                        return False, f"Table {i} must be a dictionary"
                    
                    if 'name' not in table:
                        return False, f"Table {i} missing 'name' field"
                    
                    columns = table.get('columns', [])
                    if not isinstance(columns, list):
                        return False, f"Columns for table '{table['name']}' must be a list"
                    
                    for j, column in enumerate(columns):
                        if not isinstance(column, dict):
                            return False, f"Column {j} in table '{table['name']}' must be a dictionary"
                        
                        if 'name' not in column:
                            return False, f"Column {j} in table '{table['name']}' missing 'name' field"
            else:
                # Dict format validation
                for table_name, columns in tables.items():
                    if not isinstance(columns, list):
                        return False, f"Columns for table '{table_name}' must be a list"
                    
                    for i, column in enumerate(columns):
                        if not isinstance(column, dict):
                            return False, f"Column {i} in table '{table_name}' must be a dictionary"
                        
                        if 'name' not in column:
                            return False, f"Column {i} in table '{table_name}' missing 'name' field"
            
            return True, "Schema file is valid"
            
        except yaml.YAMLError as e:
            return False, f"YAML parsing error: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def get_schema_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded schema."""
        schema_info = self.load_schema_from_yaml()
        
        summary = {
            'file_path': str(self.schema_file_path),
            'file_exists': self.schema_file_path.exists(),
            'table_count': len(schema_info),
            'total_columns': sum(len(columns) for columns in schema_info.values()),
            'tables': {}
        }
        
        for table_name, columns in schema_info.items():
            summary['tables'][table_name] = {
                'column_count': len(columns),
                'columns': [col['column_name'] for col in columns]
            }
        
        return summary
    
    def reload_schema(self) -> bool:
        """Force reload the schema from file."""
        self._schema_cache = None
        self._last_modified = None
        try:
            self.load_schema_from_yaml()
            return True
        except Exception as e:
            logger.error(f"Error reloading schema: {e}")
            return False 