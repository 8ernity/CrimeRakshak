package com.example.crimerakshak.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    // Use the Catalyst production backend URL
    private const val BASE_URL = "https://crimerakshak-backend-50044347084.development.catalystappsail.in/"

    var authToken: String? = null

    private val authInterceptor = Interceptor { chain ->
        val originalRequest = chain.request()
        val builder = originalRequest.newBuilder()
        
        authToken?.let { token ->
            builder.header("Authorization", "Bearer $token")
        }
        
        chain.proceed(builder.build())
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .build()

    val apiService: CrimeApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CrimeApiService::class.java)
    }
}
