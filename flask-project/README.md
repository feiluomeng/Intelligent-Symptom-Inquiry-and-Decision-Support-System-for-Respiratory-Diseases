# MedlinePlus Search API

这是一个Flask POST接口，用于搜索MedlinePlus健康信息。前端发送关键词，后端调用外部API并返回结果。

## 接口设计

### POST /api/search

**请求方式**: POST  
**Content-Type**: application/json

**请求参数**:
```json
{
    "keyword": "diabetes medicines"
}
```

**响应格式**:
```json
{
    "success": true,
    "keyword": "diabetes medicines",
    "encoded_keyword": "%22diabetes+medicines%22",
    "external_api_url": "https://wsearch.nlm.nih.gov/ws/query?db=healthTopics&term=%22diabetes+medicines%22",
    "results": [
        {
            "title": "Diabetes Medicines Treatment Guide",
            "summary": "Detailed information about diabetes medication treatment..."
        },
        {
            "title": "Diabetes Medicine Side Effects", 
            "summary": "Understanding potential side effects of diabetes medications..."
        }
    ]
}
```

**错误响应**:
```json
{
    "success": false,
    "error": "Error message"
}
```

## 使用方法

### 1. 启动Flask服务器

```bash
python3 app.py
```

服务器将在 `http://localhost:5000` 启动

### 2. 前端调用示例

#### JavaScript (Fetch API)
```javascript
async function searchMedlinePlus(keyword) {
    try {
        const response = await fetch('http://localhost:5000/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            console.log('Search results:', data.results);
            return data;
        } else {
            console.error('Error:', data.error);
            return null;
        }
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}

// 使用示例
searchMedlinePlus('diabetes medicines');
```

#### jQuery
```javascript
$.ajax({
    url: 'http://localhost:5000/api/search',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
        keyword: 'diabetes medicines'
    }),
    success: function(data) {
        if (data.success) {
            console.log('Search results:', data.results);
        } else {
            console.error('Error:', data.error);
        }
    },
    error: function(xhr, status, error) {
        console.error('Network error:', error);
    }
});
```

#### cURL 命令行测试
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"keyword": "diabetes medicines"}'
```

### 3. 使用前端示例页面

打开 `frontend_example.html` 文件在浏览器中，可以直接测试接口功能。

## 接口特点

1. **POST方式**: 使用POST请求发送JSON数据
2. **关键词处理**: 自动将空格替换为+号，并添加%22编码
3. **外部API调用**: 调用MedlinePlus官方API获取数据
4. **错误处理**: 完善的错误处理和响应机制
5. **CORS支持**: 可以添加CORS支持以便前端跨域访问

## 扩展功能

如需添加CORS支持，可以安装flask-cors：

```bash
pip install flask-cors
```

然后在app.py中添加：

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有域名访问
```

## 文件说明

- `app.py`: Flask后端API服务器
- `frontend_example.html`: 前端使用示例页面
- `README.md`: 使用说明文档
