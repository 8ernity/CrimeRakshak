package com.example.crimerakshak.api

import retrofit2.http.Body
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded
import retrofit2.http.GET
import retrofit2.http.POST

interface CrimeApiService {

    @FormUrlEncoded
    @POST("/api/v1/auth/login")
    suspend fun login(
        @Field("username") username: String,
        @Field("password") password: String
    ): LoginResponse

    @GET("/api/v1/analytics/districts")
    suspend fun getDistricts(): List<DistrictAnalytics>

    @GET("/api/v1/analytics/hotspots")
    suspend fun getHotspots(): List<HotspotAnalytics>

    @POST("/api/v1/chat")
    suspend fun chat(@Body request: ChatRequest): ChatResponse
}
