#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
今天吃什么 - Web服务器
提供API接口连接SQLite数据库
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import json
import psycopg2
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 云端部署配置
PORT = int(os.environ.get('PORT', 5001))

# 添加静态文件路由
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

def get_db_connection():
    """获取数据库连接"""
    # 云端部署时使用PostgreSQL
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        try:
            # PostgreSQL连接
            result = urlparse(db_url)
            conn = psycopg2.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            return conn
        except Exception as e:
            print(f"PostgreSQL连接失败，使用SQLite: {e}")
            # 如果PostgreSQL连接失败，回退到SQLite
            conn = sqlite3.connect('foods.db')
            conn.row_factory = sqlite3.Row
            return conn
    else:
        # 本地开发使用SQLite
        conn = sqlite3.connect('foods.db')
        conn.row_factory = sqlite3.Row
        return conn

@app.route('/api/random-food', methods=['GET'])
def get_random_food():
    """获取随机食物推荐"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取随机菜品
        cursor.execute('''
            SELECT d.dish_id, d.dish_name, d.category_id, d.category_name, 
                   d.restaurant_id, d.restaurant_name, d.type, d.tag, d.description, d.rating, d.created_at
            FROM dishes d 
            ORDER BY RANDOM() 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        
        if result:
            # 获取该餐厅的其他菜品名称用于标签生成
            cursor.execute('''
                SELECT dish_name FROM dishes 
                WHERE restaurant_id = ? AND dish_id != ?
                ORDER BY RANDOM() 
                LIMIT 5
            ''', (result['restaurant_id'], result['dish_id']))
            
            other_dishes = [row['dish_name'] for row in cursor.fetchall()]
            
            food = {
                'dish_id': result['dish_id'],
                'dish_name': result['dish_name'],
                'category_id': result['category_id'],
                'category_name': result['category_name'],
                'restaurant_id': result['restaurant_id'],
                'restaurant_name': result['restaurant_name'],
                'type': result['type'],
                'tag': result['tag'],
                'description': result['description'],
                'rating': result['rating'],
                'created_at': result['created_at'],
                'other_dishes': other_dishes
            }
            conn.close()
            return jsonify({'success': True, 'food': food})
        else:
            conn.close()
            return jsonify({'success': False, 'message': '没有找到菜品数据'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/foods', methods=['GET'])
def get_all_foods():
    """获取所有菜品列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.dish_id, d.dish_name, d.category_id, d.category_name, 
                   d.tag, d.description, d.rating, d.created_at
            FROM dishes d 
            ORDER BY d.dish_id
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        foods = []
        for result in results:
            foods.append({
                'dish_id': result['dish_id'],
                'dish_name': result['dish_name'],
                'category_id': result['category_id'],
                'category_name': result['category_name'],
                'tag': result['tag'],
                'description': result['description'],
                'rating': result['rating'],
                'created_at': result['created_at']
            })
        
        return jsonify({'success': True, 'foods': foods})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/foods/<int:dish_id>', methods=['GET'])
def get_food_by_id(dish_id):
    """根据ID获取菜品"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.dish_id, d.dish_name, d.category_id, d.category_name, 
                   d.tag, d.description, d.rating, d.created_at
            FROM dishes d 
            WHERE d.dish_id = ?
        ''', (dish_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            food = {
                'dish_id': result['dish_id'],
                'dish_name': result['dish_name'],
                'category_id': result['category_id'],
                'category_name': result['category_name'],
                'tag': result['tag'],
                'description': result['description'],
                'rating': result['rating'],
                'created_at': result['created_at']
            }
            return jsonify({'success': True, 'food': food})
        else:
            return jsonify({'success': False, 'message': '菜品不存在'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/foods', methods=['POST'])
def add_food():
    """添加新菜品"""
    try:
        data = request.get_json()
        
        if not all(key in data for key in ['dish_name', 'description', 'category_id', 'category_name']):
            return jsonify({'success': False, 'message': '缺少必要字段'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 生成标签和评分
        tag = data.get('tag', 'normal')
        rating = data.get('rating', 0.0)
        
        cursor.execute('''
            INSERT INTO dishes (dish_name, category_id, category_name, tag, description, rating) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['dish_name'], data['category_id'], data['category_name'], 
              tag, data['description'], rating))
        
        conn.commit()
        dish_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'dish_id': dish_id, 'message': '菜品添加成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/foods/<int:dish_id>', methods=['PUT'])
def update_food(dish_id):
    """更新菜品信息"""
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE dishes 
            SET dish_name = ?, description = ?, category_id = ?, 
                category_name = ?, tag = ?, rating = ? 
            WHERE dish_id = ?
        ''', (data['dish_name'], data['description'], data['category_id'], 
              data['category_name'], data.get('tag', 'normal'), 
              data.get('rating', 0.0), dish_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '菜品更新成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/foods/<int:dish_id>', methods=['DELETE'])
def delete_food(dish_id):
    """删除菜品"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM dishes WHERE dish_id = ?', (dish_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '菜品删除成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categories ORDER BY category_name')
        results = cursor.fetchall()
        conn.close()
        
        categories = []
        for result in results:
            categories.append({
                'category_id': result['category_id'],
                'category_code': result['category_code'],
                'category_name': result['category_name'],
                'description': result['description']
            })
        
        return jsonify({'success': True, 'categories': categories})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """获取统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 总菜品数量
        cursor.execute('SELECT COUNT(*) FROM dishes')
        total_dishes = cursor.fetchone()[0]
        
        # 按分类统计
        cursor.execute('''
            SELECT c.category_name, COUNT(d.dish_id) as count 
            FROM categories c 
            LEFT JOIN dishes d ON c.category_id = d.category_id 
            GROUP BY c.category_id, c.category_name 
            ORDER BY count DESC
        ''')
        category_stats = cursor.fetchall()
        
        # 按标签统计
        cursor.execute('''
            SELECT tag, COUNT(*) as count 
            FROM dishes 
            WHERE tag IS NOT NULL AND tag != ''
            GROUP BY tag 
            ORDER BY count DESC
        ''')
        tag_stats = cursor.fetchall()
        
        conn.close()
        
        stats = {
            'total_dishes': total_dishes,
            'category_stats': [{'category': row[0], 'count': row[1]} for row in category_stats],
            'tag_stats': [{'tag': row[0], 'count': row[1]} for row in tag_stats]
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # 检查数据库是否存在
    if not os.path.exists('foods.db'):
        print("❌ 数据库不存在，请先运行 python database.py 创建数据库")
        exit(1)
    
    print("🍽️ 今天吃什么 - Web服务器启动中...")
    print(f"📡 API服务地址: http://localhost:{PORT}")
    print(f"🔗 随机推荐: http://localhost:{PORT}/api/random-food")
    print(f"📋 所有食物: http://localhost:{PORT}/api/foods")
    print(f"📊 统计信息: http://localhost:{PORT}/api/stats")
    print("=" * 50)
    
    # 云端部署时关闭debug模式
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=PORT)
else:
    # Vercel WSGI 适配 - 当作为模块导入时（Vercel环境）
    application = app
