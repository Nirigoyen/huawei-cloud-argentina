FROM openjdk:21-slim
RUN apt-get update && apt-get install -y maven
WORKDIR /workspace
