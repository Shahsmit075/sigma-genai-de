<<<<<<< HEAD
from typing import Dict, List, Tuple, Union
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType

def detect_schema_drift(expected_schema: Dict[str, str], actual_schema: Dict[str, str]) -> Dict[str, Union[Dict[str, str], str]]:
    new_columns = {k: v for k, v in actual_schema.items() if k not in expected_schema}
    removed_columns = {k: v for k, v in expected_schema.items() if k not in actual_schema}
    type_changes = {k: (expected_schema[k], actual_schema[k]) for k in expected_schema if expected_schema[k]!= actual_schema[k]}
    
    drift_severity = 'NONE'
    if new_columns:
        if any(actual_schema[col] not in ['string', 'float'] or actual_schema[col]!='string' for col in new_columns):
            drift_severity = 'HIGH'
        else:
            drift_severity = 'LOW'
    if removed_columns:
        drift_severity = 'BREAKING'

    return {
        'new_columns': new_columns,
       'removed_columns': removed_columns,
        'type_changes': type_changes,
        'drift_severity': drift_severity
    }

def decide_action(drift_report: Dict[str, Union[Dict[str, str], str]]) -> Dict[str, Dict[str, Union[str, int]]]:
    decisions = {}
    for col_name, col_type in drift_report['new_columns'].items():
        if col_type =='string':
            decisions[col_name] = {'action': 'ADD_TO_SCHEMA','reason': 'New nullable string column', 'risk_level': 0}
        elif col_type == 'float':
            decisions[col_name] = {'action': 'FLAG_ANOMALY','reason': 'New float column', 'risk_level': 2}
        else:
            decisions[col_name] = {'action': 'ADD_TO_SCHEMA','reason': f'New column with type {col_type}', 'risk_level': 1}
    
    for col_name in drift_report['removed_columns']:
        decisions[col_name] = {'action': 'HALT','reason': 'Removed column', 'risk_level': 3}
    
    return decisions

def apply_schema_evolution(spark_df: DataFrame, decisions: Dict[str, Dict[str, Union[str, int]]], updated_schema: Dict[str, str]) -> Tuple[DataFrame, List[str]]:
    migration_notes = []
    for col_name, decision in decisions.items():
        if decision['action'] == 'DROP_SILENTLY':
            spark_df = spark_df.drop(col_name)
        elif decision['action'] == 'ADD_TO_SCHEMA':
            migration_notes.append(f"Added new column: {col_name}")
        elif decision['action'] == 'FLAG_ANOMALY':
            spark_df = spark_df.withColumn(f"{col_name}_anomaly_flag", spark_df[col_name].isNull().cast('boolean'))
            migration_notes.append(f"Flagged anomaly in column: {col_name}")
    
    return spark_df, migration_notes

def handle_drift(expected_schema: Dict[str, str], actual_schema: Dict[str, str], spark_df: DataFrame = None) -> Dict[str, Union[Dict, List, str]]:
    drift_report = detect_schema_drift(expected_schema, actual_schema)
    decisions = decide_action(drift_report)
    
    if spark_df is not None:
        spark_df, migration_notes = apply_schema_evolution(spark_df, decisions, actual_schema)
    else:
        spark_df, migration_notes = None, []
    
    print(f"Drift Report: {drift_report}")
    print(f"Decisions: {decisions}")
    print(f"Migration Notes: {migration_notes}")
    
    return {
        'drift_report': drift_report,
        'decisions': decisions,
       'migration_notes': migration_notes,
        'evolved_df': spark_df
    }
=======
from typing import Dict, List, Tuple, Any
from pyspark.sql import DataFrame
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType

def detect_schema_drift(expected_schema: Dict[str, str], actual_schema: Dict[str, str]) -> Dict[str, Any]:
    new_columns = {k: v for k, v in actual_schema.items() if k not in expected_schema}
    removed_columns = {k: v for k, v in expected_schema.items() if k not in actual_schema}
    type_changes = {k: (expected_schema[k], actual_schema[k]) for k in expected_schema if expected_schema[k]!= actual_schema[k]}
    has_drift = bool(new_columns or removed_columns or type_changes)

    drift_severity = 'NONE'
    if new_columns:
        if all('null' in v for v in new_columns.values()):
            drift_severity = 'LOW'
        else:
            drift_severity = 'HIGH'
    if removed_columns:
        drift_severity = 'BREAKING'
    if type_changes:
        drift_severity = 'HIGH'

    return {
        "new_columns": new_columns,
        "removed_columns": removed_columns,
        "type_changes": type_changes,
        "has_drift": has_drift,
        "drift_severity": drift_severity
    }

def decide_action(drift_report: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    decisions = {}
    for column, dtype in drift_report['new_columns'].items():
        if dtype =='string':
            decisions[column] = {'action': 'ADD_TO_SCHEMA','reason': 'New nullable string column', 'risk_level': 'LOW'}
        elif dtype in ['float', 'double']:
            decisions[column] = {'action': 'FLAG_ANOMALY','reason': 'New numeric column', 'risk_level': 'HIGH'}
        else:
            decisions[column] = {'action': 'ADD_TO_SCHEMA','reason': f'New nullable {dtype} column', 'risk_level': 'LOW'}
    for column in drift_report['removed_columns']:
        decisions[column] = {'action': 'HALT','reason': 'Removed column', 'risk_level': 'BREAKING'}
    for column, (old_type, new_type) in drift_report['type_changes'].items():
        if old_type!= new_type:
            if new_type == 'float' and old_type in ['int', 'long']:
                decisions[column] = {'action': 'ADD_TO_SCHEMA','reason': 'Type widening', 'risk_level': 'LOW'}
            elif new_type == 'int' and old_type == 'float':
                decisions[column] = {'action': 'FLAG_ANOMALY','reason': 'Type narrowing', 'risk_level': 'HIGH'}
    return decisions

def apply_schema_evolution(spark_df: DataFrame, decisions: Dict[str, Dict[str, str]], updated_schema: Dict[str, str]) -> Tuple[DataFrame, List[str]]:
    migration_notes = []
    for column, decision in decisions.items():
        if decision['action'] == 'DROP_SILENTLY':
            spark_df = spark_df.drop(column)
        elif decision['action'] == 'ADD_TO_SCHEMA':
            migration_notes.append(f"Added new column: {column}")
        elif decision['action'] == 'FLAG_ANOMALY':
            spark_df = spark_df.withColumn(f"{column}_anomaly", spark_df[column].isNull())
            migration_notes.append(f"Flagged anomaly in column: {column}")
        elif decision['action'] == 'HALT':
            raise ValueError(f"Schema drift would break consumers: {decision['reason']}")
    return spark_df, migration_notes

def handle_drift(expected_schema: Dict[str, str], actual_schema: Dict[str, str], spark_df: DataFrame = None) -> Dict[str, Any]:
    drift_report = detect_schema_drift(expected_schema, actual_schema)
    if not drift_report['has_drift']:
        print("No schema drift detected.")
        return drift_report
    decisions = decide_action(drift_report)
    print("Schema drift detected. Taking actions based on decisions:")
    for column, decision in decisions.items():
        print(f"Column: {column}, Action: {decision['action']}, Reason: {decision['reason']}, Risk Level: {decision['risk_level']}")
    if spark_df is not None:
        updated_schema = {**expected_schema, **{k: v for k, v in actual_schema.items() if k not in expected_schema}}
        spark_df, migration_notes = apply_schema_evolution(spark_df, decisions, updated_schema)
        print("Migration notes:")
        for note in migration_notes:
            print(note)
    drift_report['decisions'] = decisions
    return drift_report
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
