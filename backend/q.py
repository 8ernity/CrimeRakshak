import sqlite3

def run():
    conn = sqlite3.connect('crimerakshak.db')
    c = conn.cursor()
    c.execute('SELECT job_id, status, error_message, job_type FROM investigation_analysis_jobs')
    rows = c.fetchall()
    print(rows)
    conn.close()

if __name__ == "__main__":
    run()
