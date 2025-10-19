// 全局变量
let foodsData = [];
let currentFood = null;

// DOM 元素
const recommendBtn = document.getElementById('recommend-btn');
const againBtn = document.getElementById('again-btn');
const loadingDiv = document.getElementById('loading');
const resultDiv = document.getElementById('result');
const restaurantName = document.getElementById('restaurant-name');
const dishName = document.getElementById('dish-name');
const foodDescription = document.getElementById('food-description');

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    loadFoodsData();
    setupEventListeners();
});

// 加载食物数据 - 优化版本
async function loadFoodsData() {
    try {
        const response = await fetch('http://localhost:5001/api/foods');
        const data = await response.json();
        if (data.success) {
            foodsData = data.foods;
            console.log('✅ 食物数据加载成功:', foodsData.length, '种食物');
            console.log('🚀 后续推荐将使用本地数据，响应更快！');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('加载食物数据失败:', error);
        // 如果API加载失败，使用备用数据
        foodsData = getBackupFoods();
        console.log('使用备用数据:', foodsData.length, '种食物');
    }
}

// 备用食物数据（防止JSON加载失败）
function getBackupFoods() {
    return [
        {
            id: 1,
            name: "宫保鸡丁",
            description: "经典川菜，鸡肉丁配花生米，麻辣鲜香，下饭神器",
            category: "chinese",
            type: "主菜"
        },
        {
            id: 2,
            name: "意式肉酱面",
            description: "经典意面配番茄肉酱，浓郁香醇，西餐入门首选",
            category: "western",
            type: "主食"
        },
        {
            id: 3,
            name: "寿司",
            description: "新鲜生鱼片配醋饭，日式料理精髓",
            category: "japanese",
            type: "主食"
        }
    ];
}

// 设置事件监听器
function setupEventListeners() {
    recommendBtn.addEventListener('click', recommendFood);
    againBtn.addEventListener('click', recommendFood);
}

// 推荐食物主函数 - 简化版本
async function recommendFood() {
    // 显示加载动画
    showLoading();
    
    try {
        // 通过API获取随机食物
        const response = await fetch('http://localhost:5001/api/random-food');
        const data = await response.json();
        
        if (data.success) {
            currentFood = data.food;
            // 极短延迟，几乎感觉不到
            await new Promise(resolve => setTimeout(resolve, 100));
            showResult(currentFood);
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('获取随机食物失败:', error);
        alert('获取食物推荐失败，请稍后再试');
        hideLoading();
    }
}

// 显示加载动画
function showLoading() {
    loadingDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');
    recommendBtn.classList.add('hidden');
    againBtn.classList.add('hidden');
}

// 隐藏加载动画
function hideLoading() {
    loadingDiv.classList.add('hidden');
}

// 显示结果
function showResult(food) {
    // 更新餐厅名称
    restaurantName.textContent = food.restaurant_name || '未知餐厅';
    
    // 更新菜品名称
    dishName.textContent = food.dish_name || '未知菜品';
    
    // 从description数组中随机选择一条描述
    const description = getRandomDescription(food.description);
    foodDescription.textContent = description || '暂无描述';
    
    // 显示结果区域
    hideLoading();
    resultDiv.classList.remove('hidden');
    againBtn.classList.remove('hidden');
    recommendBtn.classList.add('hidden');
    
    // 添加结果动画效果
    resultDiv.style.animation = 'none';
    setTimeout(() => {
        resultDiv.style.animation = 'slideIn 0.5s ease-out';
    }, 10);
}

// 从description数组中随机选择一条描述
function getRandomDescription(description) {
    if (!description) {
        return '';
    }
    
    // 如果description是字符串，尝试解析为数组
    let descriptionArray = [];
    if (typeof description === 'string') {
        try {
            // 尝试解析JSON数组
            descriptionArray = JSON.parse(description);
        } catch (e) {
            // 如果不是JSON，按逗号分割
            descriptionArray = description.split(',').map(d => d.trim()).filter(d => d);
        }
    } else if (Array.isArray(description)) {
        descriptionArray = description;
    }
    
    // 过滤掉空字符串
    descriptionArray = descriptionArray.filter(d => d && d.trim());
    
    if (descriptionArray.length === 0) {
        return '';
    }
    
    // 随机选择一条描述
    const randomIndex = Math.floor(Math.random() * descriptionArray.length);
    return descriptionArray[randomIndex];
}

// 生成2个标签的函数（保留以备后用）
function generateTwoTags(food) {
    const tags = [];
    
    // 1. 优先取数据表中的tag
    if (food.tag && food.tag.trim()) {
        const tagList = food.tag.split(',').map(t => t.trim()).filter(t => t);
        tags.push(...tagList);
    }
    
    // 2. 如果tag数量<=2，取restaurant_name对应的菜品dish_name补齐2个tag
    if (tags.length < 2) {
        // 使用当前菜品名称
        if (food.dish_name && !tags.includes(food.dish_name)) {
            tags.push(food.dish_name);
        }
        
        // 使用该餐厅的其他菜品名称
        if (food.other_dishes && food.other_dishes.length > 0) {
            for (const dishName of food.other_dishes) {
                if (tags.length >= 2) break;
                if (!tags.includes(dishName)) {
                    tags.push(dishName);
                }
            }
        }
    }
    
    // 3. 如果tag+dish_name数量<=2，取restaurant_name对应的category_name补充2个tag
    if (tags.length < 2) {
        if (food.category_name && !tags.includes(food.category_name)) {
            tags.push(food.category_name);
        }
    }
    
    // 确保返回2个标签，不足的用空字符串补齐
    while (tags.length < 2) {
        tags.push('');
    }
    
    return tags.slice(0, 2);
}

// 隐藏结果
function hideResult() {
    resultDiv.classList.add('hidden');
    againBtn.classList.add('hidden');
    recommendBtn.classList.remove('hidden');
}

// 获取分类中文名称
function getCategoryName(category) {
    const categoryNames = {
        'dongbei': '东北菜',
        'sichuan': '川菜',
        'hunan': '湘菜',
        'jiangzhe': '江浙菜',
        'fastfood': '快餐',
        'japanese': '日料',
        'yungui': '云贵菜',
        'healthy': '健康餐'
    };
    return categoryNames[category] || category;
}

// 添加键盘支持
document.addEventListener('keydown', function(event) {
    // 按空格键或回车键推荐食物
    if (event.code === 'Space' || event.code === 'Enter') {
        event.preventDefault();
        if (!loadingDiv.classList.contains('hidden')) {
            return; // 如果正在加载，不响应
        }
        recommendFood();
    }
});

// 添加触摸支持（移动端）
let touchStartY = 0;
let touchEndY = 0;

document.addEventListener('touchstart', function(event) {
    touchStartY = event.changedTouches[0].screenY;
});

document.addEventListener('touchend', function(event) {
    touchEndY = event.changedTouches[0].screenY;
    handleSwipe();
});

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartY - touchEndY;
    
    // 向上滑动推荐食物
    if (diff > swipeThreshold && !loadingDiv.classList.contains('hidden')) {
        recommendFood();
    }
}

// 添加一些有趣的交互效果
function addFunEffects() {
    // 为按钮添加点击波纹效果
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// 页面加载完成后添加特效
document.addEventListener('DOMContentLoaded', function() {
    addFunEffects();
});

// 添加波纹效果的CSS（通过JavaScript动态添加）
const style = document.createElement('style');
style.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.6);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
