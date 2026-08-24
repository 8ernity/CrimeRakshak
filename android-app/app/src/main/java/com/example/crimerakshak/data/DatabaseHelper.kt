package com.example.crimerakshak.data

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.io.File
import java.io.FileOutputStream

class DatabaseHelper(private val context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    companion object {
        private const val DATABASE_NAME = "crimerakshak.db"
        private const val DATABASE_VERSION = 1
    }

    private val dbPath = context.getDatabasePath(DATABASE_NAME).absolutePath

    init {
        copyDatabaseIfNeeded()
    }

    private fun copyDatabaseIfNeeded() {
        val dbFile = File(dbPath)
        if (!dbFile.exists()) {
            dbFile.parentFile?.mkdirs()
            context.assets.open("databases/$DATABASE_NAME").use { inputStream ->
                FileOutputStream(dbFile).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
        }
    }

    override fun onCreate(db: SQLiteDatabase) {
        // Pre-populated database, so onCreate is empty
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        if (newVersion > oldVersion) {
            val dbFile = File(dbPath)
            if (dbFile.exists()) {
                dbFile.delete()
            }
            copyDatabaseIfNeeded()
        }
    }

    fun runQuery(sql: String): List<Map<String, Any>> {
        val db = this.readableDatabase
        val cursor = db.rawQuery(sql, null)
        val result = mutableListOf<Map<String, Any>>()
        
        if (cursor.moveToFirst()) {
            do {
                val row = mutableMapOf<String, Any>()
                for (i in 0 until cursor.columnCount) {
                    val columnName = cursor.getColumnName(i)
                    when (cursor.getType(i)) {
                        android.database.Cursor.FIELD_TYPE_INTEGER -> row[columnName] = cursor.getLong(i)
                        android.database.Cursor.FIELD_TYPE_FLOAT -> row[columnName] = cursor.getDouble(i)
                        android.database.Cursor.FIELD_TYPE_STRING -> row[columnName] = cursor.getString(i)
                        android.database.Cursor.FIELD_TYPE_NULL -> row[columnName] = "NULL"
                        else -> row[columnName] = cursor.getString(i) ?: ""
                    }
                }
                result.add(row)
            } while (cursor.moveToNext())
        }
        cursor.close()
        return result
    }
}
