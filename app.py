# 先安装依赖：pip install flask python-dotenv werkzeug
import os
from flask import Flask, render_template, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import time

# 初始化 Flask 应用
app = Flask(__name__)

# 核心配置（不用改，本地测试用）
UPLOAD_FOLDER = "./my_netdisk_files"  # 文件存储目录，自动生成
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv'}  # 支持的文件类型
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 最大上传100MB
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 创建存储文件夹（不存在则自动建）
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 检查文件类型是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 首页：展示网盘界面+加载文件列表
@app.route('/')
def index():
    files = []
    if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path):
                # 获取文件信息
                file_size = round(os.path.getsize(file_path) / 1024 / 1024, 2)  # 转MB
                file_mtime = time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(file_path)))
                file_type = 'image' if filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'} else 'video'
                files.append({
                    'name': filename,
                    'size': file_size,
                    'mtime': file_mtime,
                    'type': file_type
                })
    # 把文件列表传给前端
    return render_template('index.html', files=files)

# 上传文件接口（前端调用）
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'msg': '未选择文件'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'msg': '文件名不能为空'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # 安全处理文件名
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'success': True, 'msg': '上传成功'}), 200
    else:
        return jsonify({'success': False, 'msg': '仅支持图片/视频格式'}), 400

# 下载文件接口
@app.route('/download/<filename>')
def download_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'msg': f'下载失败：{str(e)}'}), 500

# 删除文件接口
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({'success': True, 'msg': '删除成功'}), 200
        else:
            return jsonify({'success': False, 'msg': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'msg': f'删除失败：{str(e)}'}), 500

# 预览文件接口（图片/视频直接访问）
@app.route('/files/<filename>')
def preview_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 启动应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # 0.0.0.0允许外网访问