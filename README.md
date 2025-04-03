# 包管理器后端

## 接口说明

1. `GET`--`/repo`
    - **描述:** 获取`upload`目录下的`repo.json`

2. `GET`--`/download`
    - **描述:** 下载指定包
    - **参数:**
        - `Query`: `name`=`?`

3. `POST`--`/update`
    - **描述:** 上传包, 必须是以`.tar.gz`或者`.zip`结尾的压缩包, 包内要含有名为`wfuzz-package.json`的`json`文件
    - **参数:** 
        - `Header`: `Content-type`=`multipart/form-data`
        - `Body`: `file`=`xxx.tar.gz`
    - **测试:**
        - 将目录中提供的`wfuzz-code.tar.gz`上传后, 在`upload/repo.json`中的`data`字段的末尾会多出`wfuzz-code`包的相关信息

## 项目目录

```bash
--wfuzz-package-manager
|
|--wfuzz-server
|  |--upload/    
|  |  |--repo.json
|  |--README.md
|  |--server.py
|
|--wfuzz-client
|  |--src/
|  |--Cargo.lock
|  |--Cargo.toml
|  |--wfuzz-code.tar.gz   # 用于测试上传的包
|
```
