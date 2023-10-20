use axum::Router;
use axum::body::Body;
use axum::routing::post;
use axum::AddExtensionLayer;
use axum::http::Response;
use axum::http::Request;
use axum::http::StatusCode;
use rand::Rng;
use tokio;
use serde::Deserialize;

#[derive(Deserialize)]
struct Payload {
    key: String,
}

async fn handle_post(_input: Request<Body>) -> Result<Response<Body>, StatusCode> {
    let charset: &[u8] = b"ABCDEF0123456789";
    let mut rng = rand::thread_rng();
    let string_length = rng.gen_range(4000..5000);
    let random_string: String = (0..string_length)
     .map(|_| { charset[rng.gen_range(0..charset.len())] as char })
     .collect();
    return Ok(Response::new(format!(r#"{{"message":"{bytes}"}}"#, bytes=random_string).into()));
}

#[tokio::main]
async fn main() {

    let app = Router::new()
        .route("/c1", post(handle_post))
        .route("/c2", post(handle_post))
        .route("/c3", post(handle_post))
        .layer(AddExtensionLayer::new(()));
    axum::Server::bind(&"0.0.0.0:7070".parse().unwrap())
        .serve(app.into_make_service())
        .await
        .unwrap();
}