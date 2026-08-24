package com.example.crimerakshak.api

import com.google.gson.annotations.SerializedName

data class LoginResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("token_type")
    val tokenType: String? = null
)

data class ChatRequest(
    val message: String,
    @SerializedName("conversation_id")
    val conversationId: String? = null,
    val language: String = "en"
)

data class ChatResponse(
    @SerializedName("conversation_id")
    val conversationId: String,
    val answer: String,
    val language: String = "en"
)

data class DistrictAnalytics(
    val name: String,
    val range: String,
    val ipc: Int,
    val sll: Int,
    val total: Int
)

data class HotspotAnalytics(
    val district: String,
    val total: Int,
    val murder: Int,
    val robbery: Int,
    val theft: Int,
    val riots: Int,
    @SerializedName("casesOfHurt")
    val casesOfHurt: Int,
    @SerializedName("cyberCrime")
    val cyberCrime: Int
)

data class SQLQueryRequest(
    val sql: String,
    @SerializedName("max_rows")
    val maxRows: Int = 500
)

data class SQLQueryResponse(
    val columns: List<String>,
    val rows: List<Map<String, Any>>,
    @SerializedName("row_count")
    val rowCount: Int,
    val sql: String,
    val truncated: Boolean
)


