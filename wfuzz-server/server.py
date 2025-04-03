import os
import json
import hashlib
import tarfile
import zipfile
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

UPLOAD_FOLDER = "upload/"
TEMP_FOLDER = "temp_extract/"
REPO_FILE = UPLOAD_FOLDER + "repo.json"
HTTP_SERVER = os.getenv('HTTP_SERVER', "http://127.0.0.1:8080")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

if not os.path.exists(REPO_FILE):
    with open(REPO_FILE, 'w') as f:
        json.dump({"code": 0, "data": [], "message": "OK"}, f)


"""计算file的哈希值"""
def calculate_sha1(file):
    sha1 = hashlib.sha1()
    chunk_size = 4096
    while chunk := file.read(chunk_size):
        sha1.update(chunk)
    file.seek(0)
    return sha1.hexdigest()

"""解压文件并读取wfuzz-package.json的元数据"""
def extract_and_read_metadata(file, filename):
    if not file:
        raise ValueError("Invalid file object")

    # 创建临时目录
    temp_dir = os.path.join(TEMP_FOLDER, filename)
    os.makedirs(temp_dir, exist_ok=True)

    # 将文件保存在临时目录下
    temp_file = os.path.join(temp_dir, filename)
    file.save(temp_file)

    metadata, file_size = None, os.path.getsize(temp_file)
    if file_size == 0:
        raise ValueError("file uploaded is empty")

    try:
        # 解压文件 
        if filename.endswith('.tar.gz'):
            with tarfile.open(temp_file) as tar:
                tar.extractall(temp_dir)
        elif filename.endswith('.zip'):
            with zipfile.ZipFile(temp_file) as zip:
                zip.extractall(temp_dir)

        # 查找wfuzz-package.json文件
        for root, _, files in os.walk(temp_dir):
            if 'wfuzz-package.json' in files:
                with open(os.path.join(root, 'wfuzz-package.json')) as f:
                    metadata = json.load(f)
                break
    except Exception as e:
        app.logger.error(f"extract failed: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        if os.path.exists(temp_dir):
            for root, dirs, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(temp_dir)

    return metadata, file_size

@app.route('/update', methods=['POST'])
def upload_package():
    """上传包"""

    ""
    if "file" not in request.files:
        return jsonify({
            "code": 400,
            "message": "No file part",
            "data": None
        }), 400

    ""
    file = request.files["file"]
    if file.filename == '':
        return jsonify({
            "code": 400,
            "message": "No selected file",
            "data": None
        }), 400
    
    ""
    if file and (file.filename.endswith('.tar.gz') or file.filename.endswith('.zip')):

        # 计算文件大小和sha1
        sha1sum = calculate_sha1(file)

        # 解压文件并读取wfuzz-package.json元数据
        metadata, file_size = extract_and_read_metadata(file, file.filename)
        file.seek(0)
        if not metadata:
            return jsonify({
                "code": 400,
                "message": "Missing package metadata",
                "data": None
            }), 400
        
        # 保存包文件
        package_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(package_path)

        # 更新repo.json
        with open(REPO_FILE, 'r+') as f:
            repo_data = json.load(f)
            packages = repo_data["data"]

            # 创建版本信息
            version_info = {
                "dependencies": metadata.get("dependencies", []),
                "sha1sum": sha1sum,
                "size": file_size,
                "url": f"{HTTP_SERVER}/download?name={file.filename}",
                "version": metadata["version"]
            }

            # 查找是否已存在同名的包
            pkg_idx = next((i for i, p in enumerate(packages) if p["name"] == metadata["name"]), None)
            if pkg_idx is not None:
                # 更新现有的包
                cur_pkg = packages[pkg_idx]
                cur_pkg["description"] = metadata.get("description", cur_pkg["description"])

                # 检查是否存在相同的版本
                version_idx = next((i for i, v in enumerate(cur_pkg["versions"]) if v["version"] == version_info["version"]), None)
                if version_idx is not None:
                    cur_pkg["versions"][version_idx] = version_info
                else:
                    cur_pkg["versions"].append(version_info)
            else:
                # 否则创建新的包
                new_package = {
                    "description": metadata.get("description", ""),
                    "name": metadata["name"],
                    "version": [version_info]
                }
                packages.append(new_package)
            
            f.seek(0)
            json.dump(repo_data, f, indent=2)
            f.truncate()
        
        return jsonify({
            "code": 200,
            "message": "Package uploaded successfully",
            "data": {
                "name": metadata["name"],
                "version": version_info["version"]
            }
        }), 200
    
    ""
    return jsonify({
        "code": 400,
        "message": "Invalid file format, only .tar.gz or .zip accepted",
        "data": None
    }), 400


@app.route('/repo', methods=['GET'])
def get_repo():
    """返回包列表"""
    with open(REPO_FILE, 'r') as f:
        repo_data = json.load(f)
    return jsonify(repo_data)


@app.route('/download', methods=['GET'])
def download_package():
    """下载包"""
    package_name = request.args.get('name')
    if not package_name:
        return jsonify({"code": 400, "message": "Missing package name", "data": None}), 400

    package_path = os.path.join(UPLOAD_FOLDER, package_name)
    if not os.path.exists(package_path):
        return jsonify({"code": 404, "message": "Package not found", "data": None}), 404
    
    return send_from_directory(UPLOAD_FOLDER, package_name, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    # json.dump()
