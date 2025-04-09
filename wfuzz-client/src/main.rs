mod tcp_client;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // TODO: 命令
    Ok(())
}

#[tokio::test]
async fn test_upload() -> Result<(), Box<dyn std::error::Error>> {
    // 上传包
    tcp_client::upload_package("wfuzz-code.tar.gz", r#"{"name": "wfuzz-code", "version": "1.10.14.0"}"#).await?;
    Ok(())
}

#[tokio::test]
async fn test_get_package() -> Result<(), Box<dyn std::error::Error>>  {
    // 获取包列表
    let package = tcp_client::get_package_list().await?;
    println!("Package list: {:#?}", package);
    Ok(())
}

#[tokio::test]
async fn test_download() -> Result<(), Box<dyn std::error::Error>> {
    // 下载包
    tcp_client::download_package("wfuzz-code.tar.gz").await?;
    Ok(())
}

mod learn;