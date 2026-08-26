import sqlite3
conn = sqlite3.connect('crimerakshak.db')
conn.execute("UPDATE investigation_analysis_jobs SET status='failed', error_message='Backend restarted' WHERE status='processing' OR status='queued'")
conn.commit()
conn.close()
