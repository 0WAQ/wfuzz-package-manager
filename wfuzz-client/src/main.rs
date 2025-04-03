use reqwest::multipart;
use serde_json::Value;
use std::fs::File;
use std::path::Path;
use tokio::fs::File as AsyncFile;
use tokio::io::AsyncReadExt;

const HTTP_SERVER: &str = "http://127.0.0.1:8080";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // TODO: 命令
    Ok(())
}

#[tokio::test]
async fn test_upload() -> Result<(), Box<dyn std::error::Error>> {
    // 上传包
    upload_package("wfuzz-code.tar.gz", r#"{"name": "wfuzz-code", "version": "1.10.14.0"}"#).await?;
    Ok(())
}

#[tokio::test]
async fn test_get_package() -> Result<(), Box<dyn std::error::Error>>  {
    // 获取包列表
    let package = get_package_list().await?;
    println!("Package list: {:#?}", package);
    Ok(())
}

#[tokio::test]
async fn test_download() -> Result<(), Box<dyn std::error::Error>> {
    // 下载包
    download_package("wfuzz-code.tar.gz").await?;
    Ok(())
}

/// 上传包文件 
#[allow(dead_code)]
#[allow(unused_variables)]
async fn upload_package(filepath: &str, metadata: &str) 
    -> Result<(), Box<dyn std::error::Error>>
{
    let client = reqwest::Client::new();

    // 异步读取文件内容
    let mut file = AsyncFile::open(filepath).await?;
    let mut file_content = Vec::new();
    file.read_to_end(&mut file_content).await?;

    // 获取文件名并处理None
    let filename = Path::new(filepath)
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_owned();

    // 创建文件部分
    let file_part = multipart::Part::bytes(file_content)
        .file_name(filename)
        .mime_str("application/octet-stream")?;

    // 创建multipart表单
    let form = multipart::Form::new()
        .part("file", file_part)
        .text("metadata", metadata.to_owned());

    // 发送请求    
    let response = client
        .post(&format!("{}/update", HTTP_SERVER))
        .multipart(form)
        .send()
        .await?;

    Ok(())
}

/// 获取包列表
#[allow(dead_code)]
#[allow(unused_variables)]
async fn get_package_list() -> Result<Value, Box<dyn std::error::Error>> {
    let response = reqwest::get(&format!("{}/repo", HTTP_SERVER))
        .await?
        .json::<Value>()
        .await?;

    Ok(response)
}

/// 下载包文件
#[allow(dead_code)]
#[allow(unused_variables)]
async fn download_package(package_name: &str)
    -> Result<(), Box<dyn std::error::Error>>
{
    // 发送http请求并接收响应
    let response = reqwest::get(&format!("{}/download?name={}", HTTP_SERVER, package_name))
        .await?;

    // 创建下载目录并返回
    let mut download_dir = get_and_create_dir(package_name)?;

    // 读取内容并写入文件
    let mut content = std::io::Cursor::new(response.bytes().await?);
    _ = std::io::copy(&mut content, &mut download_dir);

    Ok(())
}

/// 从创建下载文件
fn get_and_create_dir(package_name: &str) -> std::io::Result<File> {
    let download_dir = std::env::current_dir().unwrap();
    let mut download_dir = String::from(download_dir.to_str().unwrap());
    download_dir += "download_package/";

    // 创建目录
    _ = std::fs::create_dir(&download_dir);

    // 创建文件
    download_dir.push_str(package_name);
    let file = std::fs::File::create(&download_dir);

    file
}