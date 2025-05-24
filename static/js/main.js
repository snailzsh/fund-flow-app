// 全局变量
let currentDataType = 'industry'; // 'industry' 或 'concept'
let currentPeriod = 'today';      // 'today', '5days', 或 '10days'
let currentData = [];             // 当前显示的数据
let autoRefreshTimer = null;      // 自动刷新计时器
let lastUpdateCheckTimer = null;  // 最后更新时间检查计时器

// 统一的金额格式化函数，支持负值高亮
function formatBillion(value) {
    const num = parseFloat(value);
    if (isNaN(num)) return "-";
    const fixed = num.toFixed(2);
    return fixed;
}

// 格式化金额并返回带颜色类的值
function formatBillionWithClass(value) {
    const num = parseFloat(value);
    if (isNaN(num)) return { value: "-", className: "" };
    const fixed = num.toFixed(2);
    return {
        value: fixed,
        className: num >= 0 ? 'positive' : 'negative'
    };
}

// 格式化百分比
function formatPercent(value) {
    if (typeof value === 'string' && value.includes('%')) {
        return value;
    }
    const num = parseFloat(value);
    if (isNaN(num)) return "-";
    return (num * 100).toFixed(2) + '%';
}

// 页面加载完成后执行
$(document).ready(function() {
    console.log("页面加载完成，准备初始化...");
    
    // 首先测试API连通性
    testApiConnection();
    
    // 初始加载数据
    loadData();
    
    // 绑定事件处理函数
    bindEvents();
    
    // 启动自动检查最后更新时间
    startUpdateTimeCheck();
});

// 测试API连通性
function testApiConnection() {
    console.log("测试API连通性...");
    $.ajax({
        url: '/api/test',
        method: 'GET',
        success: function(data) {
            console.log("API连通性测试成功:", data);
        },
        error: function(error) {
            console.error("API连通性测试失败:", error);
        }
    });
}

// 绑定事件处理函数
function bindEvents() {
    console.log("绑定事件处理函数...");
    
    // 时间区间切换
    $('#timeRangeTab a').on('click', function(e) {
        e.preventDefault();
        $('#timeRangeTab a').removeClass('active');
        $(this).addClass('active');
        currentPeriod = $(this).data('period');
        console.log("切换时间周期:", currentPeriod);
        loadData();
    });
    
    // 板块类型切换
    $('#industryBtn').on('click', function() {
        currentDataType = 'industry';
        $(this).addClass('active').removeClass('btn-outline-secondary').addClass('btn-secondary');
        $('#conceptBtn').removeClass('active').removeClass('btn-secondary').addClass('btn-outline-secondary');
        console.log("切换到行业板块");
        loadData();
    });
    
    $('#conceptBtn').on('click', function() {
        currentDataType = 'concept';
        $(this).addClass('active').removeClass('btn-outline-secondary').addClass('btn-secondary');
        $('#industryBtn').removeClass('active').removeClass('btn-secondary').addClass('btn-outline-secondary');
        console.log("切换到概念板块");
        loadData();
    });
    
    // 手动刷新数据
    $('#refreshBtn').on('click', function() {
        console.log("手动刷新数据");
        loadData();
    });
    
    // 搜索功能
    $('#searchBtn').on('click', function() {
        console.log("执行搜索");
        filterData();
    });
    
    $('#searchInput').on('keyup', function(e) {
        if (e.key === 'Enter') {
            console.log("按Enter键搜索");
            filterData();
        }
    });
    
    // 表格排序
    $('.sortable').on('click', function() {
        const sortField = $(this).data('sort');
        console.log("按字段排序:", sortField);
        sortData(sortField);
    });
    
    // 自动刷新设置
    $('#autoRefreshCheck').on('change', function() {
        if ($(this).prop('checked')) {
            console.log("启动自动刷新");
            startAutoRefresh();
        } else {
            console.log("停止自动刷新");
            stopAutoRefresh();
        }
    });
    
    $('#refreshInterval').on('change', function() {
        if ($('#autoRefreshCheck').prop('checked')) {
            console.log("更新自动刷新间隔");
            stopAutoRefresh();
            startAutoRefresh();
        }
    });
    
    // 导出功能 - 使用服务器端导出
    $('#exportExcel').on('click', function() {
        const url = `/export/excel?type=${currentDataType}&period=${currentPeriod}`;
        console.log("导出Excel:", url);
        window.open(url, '_blank');
    });
    
    $('#exportCSV').on('click', function() {
        const url = `/export/csv?type=${currentDataType}&period=${currentPeriod}`;
        console.log("导出CSV:", url);
        window.open(url, '_blank');
    });
}

// 加载数据
function loadData() {
    // 显示加载指示器
    $('#tableBody').html('<tr><td colspan="8" class="text-center">加载中...</td></tr>');
    
    // 根据当前数据类型选择API端点
    const endpoint = currentDataType === 'industry' ? '/api/industry_data' : '/api/concept_data';
    console.log(`正在从 ${endpoint} 加载数据，时间周期: ${currentPeriod}`);
    
    // 发送AJAX请求
    $.ajax({
        url: endpoint,
        method: 'GET',
        data: { period: currentPeriod },
        dataType: 'json',
        success: function(data) {
            console.log(`成功加载数据，共 ${data ? data.length : 0} 条记录`);
            
            // 保存数据并渲染表格
            if (data && Array.isArray(data)) {
                currentData = data;
                renderTable(currentData);
            } else {
                console.error("加载的数据不是数组:", data);
                $('#tableBody').html('<tr><td colspan="8" class="text-center text-danger">数据格式错误</td></tr>');
            }
            
            // 更新最后更新时间
            checkLastUpdate();
        },
        error: function(error) {
            console.error('数据加载失败:', error);
            $('#tableBody').html('<tr><td colspan="8" class="text-center text-danger">数据加载失败，请稍后重试</td></tr>');
        }
    });
}

// 渲染表格
function renderTable(data) {
    console.log("开始渲染表格");
    const tbody = $('#tableBody');
    tbody.empty();
    
    // 没有数据时显示提示
    if (!data || data.length === 0) {
        console.log("没有数据可显示");
        tbody.html('<tr><td colspan="8" class="text-center">暂无数据</td></tr>');
        return;
    }
    
    // 限制显示前20条数据
    const displayData = data.slice(0, 20);
    console.log(`显示前 ${displayData.length} 条数据`);
    
    displayData.forEach((item, index) => {
        try {
            const tr = $('<tr></tr>');
            
            // 构建表格行
            tr.append(`<td>${index + 1}</td>`);
            tr.append(`<td>${item.name || '未知'}</td>`);
            
            // 涨跌幅 - 根据正负值添加颜色
            const changePercent = formatPercent(item.change_percent);
            const changeValue = parseFloat(item.change_percent) || 0;
            const changeClass = changeValue >= 0 ? 'positive' : 'negative';
            tr.append(`<td class="${changeClass}">${changePercent}</td>`);
            
            // 主力净流入 - 已经是亿元单位，直接格式化
            const mainNetInflowFormatted = formatBillionWithClass(item.main_inflow || item.main_net_inflow || 0);
            tr.append(`<td class="${mainNetInflowFormatted.className}">${mainNetInflowFormatted.value}亿</td>`);
            
            // 主力净流入率
            const mainInflowPercent = item.main_net_ratio || formatPercent(item.main_inflow_percent || 0);
            tr.append(`<td>${mainInflowPercent}</td>`);
            
            // 超大单净流入 - 已经是亿元单位，直接格式化
            const superNetInflowFormatted = formatBillionWithClass(item.super_large_inflow || item.super_net_inflow || 0);
            tr.append(`<td class="${superNetInflowFormatted.className}">${superNetInflowFormatted.value}亿</td>`);
            
            // 超大单净流入率
            const superInflowPercent = item.super_net_ratio || formatPercent(item.super_large_inflow_percent || 0);
            tr.append(`<td>${superInflowPercent}</td>`);
            
            // 主力净流入最大股
            tr.append(`<td>${item.stock_name || item.top_stock || '未知'}</td>`);
            
            tbody.append(tr);
        } catch (e) {
            console.error(`渲染第 ${index + 1} 行数据时出错:`, e, item);
        }
    });
    
    console.log("表格渲染完成");
}

// 过滤数据
function filterData() {
    const searchTerm = $('#searchInput').val().toLowerCase().trim();
    console.log(`执行过滤，搜索词: "${searchTerm}"`);
    
    if (!searchTerm) {
        renderTable(currentData);
        return;
    }
    
    const filteredData = currentData.filter(item => 
        (item.name && item.name.toLowerCase().includes(searchTerm)) || 
        (item.top_stock && item.top_stock.toLowerCase().includes(searchTerm))
    );
    
    console.log(`过滤后数据: ${filteredData.length} 条记录`);
    renderTable(filteredData);
}

// 排序数据
function sortData(field) {
    // 查找当前排序列和方向
    const th = $(`.sortable[data-sort="${field}"]`);
    const currentIcon = th.find('.sort-icon').text();
    
    // 清除所有排序图标
    $('.sort-icon').text('');
    
    // 确定排序方向
    const isAsc = currentIcon === '↓' ? true : false;
    th.find('.sort-icon').text(isAsc ? '↑' : '↓');
    
    console.log(`按字段 ${field} 排序，方向: ${isAsc ? '升序' : '降序'}`);
    
    // 执行排序
    try {
        currentData.sort((a, b) => {
            let valA, valB;
            
            // 映射新旧字段名
            let actualField = field;
            if (field === 'main_net_inflow') {
                actualField = 'main_inflow';
            } else if (field === 'main_net_ratio') {
                actualField = 'main_inflow_percent';
            } else if (field === 'super_net_inflow') {
                actualField = 'super_large_inflow';
            } else if (field === 'super_net_ratio') {
                actualField = 'super_large_inflow_percent';
            }
            
            if (typeof a[actualField] === 'string' && a[actualField].includes('%')) {
                valA = parseFloat(a[actualField].replace('%', '')) || 0;
            } else {
                valA = a[actualField] || 0;
            }
            
            if (typeof b[actualField] === 'string' && b[actualField].includes('%')) {
                valB = parseFloat(b[actualField].replace('%', '')) || 0;
            } else {
                valB = b[actualField] || 0;
            }
            
            if (isAsc) {
                return valA - valB;
            } else {
                return valB - valA;
            }
        });
        
        renderTable(currentData);
    } catch (e) {
        console.error(`排序时出错:`, e);
    }
}

// 启动自动刷新
function startAutoRefresh() {
    const interval = parseInt($('#refreshInterval').val()) * 1000;
    
    stopAutoRefresh();
    
    console.log(`启动自动刷新，间隔: ${interval}ms`);
    autoRefreshTimer = setInterval(() => {
        loadData();
    }, interval);
}

// 停止自动刷新
function stopAutoRefresh() {
    if (autoRefreshTimer) {
        clearInterval(autoRefreshTimer);
        autoRefreshTimer = null;
        console.log("停止自动刷新");
    }
}

// 检查最后更新时间
function checkLastUpdate() {
    console.log("检查最后更新时间");
    $.ajax({
        url: '/api/last_update',
        method: 'GET',
        success: function(data) {
            $('#lastUpdateTime').text(data.last_update || "未知");
            console.log(`最后更新时间: ${data.last_update}`);
        },
        error: function(error) {
            console.error('获取最后更新时间失败:', error);
        }
    });
}

// 启动自动检查最后更新时间
function startUpdateTimeCheck() {
    // 每分钟检查一次最后更新时间
    lastUpdateCheckTimer = setInterval(() => {
        checkLastUpdate();
    }, 60000);
    console.log("启动自动检查最后更新时间，间隔: 60秒");
}

// 页面关闭时清理定时器
$(window).on('beforeunload', function() {
    stopAutoRefresh();
    if (lastUpdateCheckTimer) {
        clearInterval(lastUpdateCheckTimer);
    }
});
