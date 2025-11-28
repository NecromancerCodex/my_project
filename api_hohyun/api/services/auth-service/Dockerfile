# 빌드 단계
FROM gradle:8.14-jdk21 AS builder
WORKDIR /build
COPY . .
RUN gradle :services:auth-service:build -x test

# 실행 단계 (slim 버전 사용)
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /build/services/auth-service/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]