
import ctypes
import json
import pymysql
import os

mysql_conn = pymysql.connect(host='139.199.0.99', user='root', password='root', port=3306, database='rrmh',
                                          charset='utf8')
# 调用C接口
project_dir = '/home/ubuntu/manhua_spider/manhua'
image_dir = project_dir + '/images/' + 'full/test.jpg'
c_path1 = project_dir + '/libfdfs_upload_file.so'
c_path2 = '/usr/lib/libfdfsclient.so'
ctypes.CDLL(c_path2,mode=ctypes.RTLD_GLOBAL)
libc = ctypes.cdll.LoadLibrary(c_path1)
myUpload = libc.myUpload  # 取函数
myUpload.restype = ctypes.c_int  # 定义函数返回值
# 三个参数
confFile = bytes('/etc/fdfs/client.conf', encoding='utf-8')
localFile = bytes(image_dir, encoding='utf-8')
fileID = ctypes.create_string_buffer(80)
a = myUpload(confFile, localFile, fileID)
if a==0:
    print('文件上传成功')
    # 传入数据库
    data = dict()
    data['iamge_id'] = str(fileID.value)
    json_data = json.dumps(data)
    cursor = mysql_conn.cursor()
    cursor.execute('INSERT INTO json_page (json) VALUES (%s)', (str(json_data)))
    mysql_conn.commit()
    cursor.close()
    print('传入成功')
    os.remove(image_dir)
mysql_conn.close()
