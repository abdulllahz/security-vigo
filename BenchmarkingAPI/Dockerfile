FROM rust:latest AS builder
WORKDIR /app
COPY . .
RUN cargo build --release
FROM rust:latest
WORKDIR /app
COPY --from=builder /app/target/release/app .
EXPOSE 7070
CMD ["./app"]