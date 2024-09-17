document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchCancelButton = document.getElementById('search-cancel');
    const searchResultWrapper = document.getElementById('search-result-wrapper');
    const searchResultsContainer = document.getElementById('search-results');
    let debounceTimer;  // 用于存储去抖动定时器
    let query = '';  // 用于存储当前搜索的查询字符串
    let currentPage = 1;


    // 监听搜索表单的提交事件
    searchInput.addEventListener('input', function() {
        // 设置去抖动 debounce 机制，防止用户快速输入时多次触发请求
        clearTimeout(debounceTimer);  // 清除上一次的定时器
        debounceTimer = setTimeout(function() {
            query = searchInput.value.trim();
            console.log('Fetching results for query:', query);  // 添加调试
            if (query.length > 0) {
                // 显示取消按钮
                searchCancelButton.classList.remove('d-none');
                currentPage = 1;  // 重置到第一页
                // 发起搜索请求
                fetchResults(query, currentPage);
            } else {
                // 清空搜索结果容器
                searchResultsContainer.innerHTML = '';

                // 隐藏搜索结果容器
                searchResultWrapper.classList.add('d-none');

                // 显示当前页面之前内容
                document.querySelector("div.row.flex-grow-1")?.classList.remove('d-none');
                document.querySelector("#main-wrapper > div > div:nth-child(3)")?.classList.remove('d-none');
            }
        }, 300);  // 延迟 300 毫秒 发起请求
    });

    // 发送 Ajax 请求获取特定页的数据
    function fetchResults(query, page) {
        console.log('Fetching results for query:', query);  // 添加调试
        console.log('Fetching results for page:', page);
        fetch(`/search/?q=${encodeURIComponent(query)}&page=${page}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            console.log('Search data:', data.results);  // 打印数据
            if (data.results && data.results.length > 0) {  // 空数组 [] 在 JavaScript 中被视为 truthy 值，所以需要检查长度
                searchResultsContainer.innerHTML = data.results_html;  // 显示当前页数据及更新分页链接
                console.log('Search results updated:', searchResultsContainer);  // 添加调试
//                sessionStorage.setItem('searchResults', data.results_html);
//                sessionStorage.setItem('searchQuery', query);
//                history.pushState(null, '', pageUrl);  // 更新 URL，但不要刷新页面

                // 隐藏当前页面部分内容
                document.querySelector("div.row.flex-grow-1")?.classList.add('d-none');
                document.querySelector("#main-wrapper > div > div:nth-child(3)")?.classList.add('d-none');
                // 显示搜索结果容器
                searchResultWrapper.classList.remove('d-none');
            } else {
                // 没有结果时显示提示
                searchResultsContainer.innerHTML = '<p class="row justify-content-center">呜呜~没有找到结果</p>';
                searchResultWrapper.classList.remove('d-none');
                console.error('No HTML found in response data.');
             }
        }).catch(error => {
            // 请求失败时的提示信息
            searchResultsContainer.innerHTML = '<p class="row justify-content-center">搜索请求失败，请稍后再试</p>';
            console.error('搜索请求失败:', error);
        });
    }

     // 取消按钮事件
    searchCancelButton.addEventListener('click', function() {
      searchInput.value = '';
      searchResultsContainer.innerHTML = ''; // 清空结果容器
      searchResultWrapper.classList.add('d-none');
      searchCancelButton.classList.add('d-none');

      // 显示当前页面之前的内容
      document.querySelector("div.row.flex-grow-1")?.classList.remove('d-none');
      document.querySelector("#main-wrapper > div > div:nth-child(3)")?.classList.remove('d-none');

      // 如果你想要回到之前的页面，可以考虑使用 history.back() 或 history.go(-1)
      // history.back();  // 返回到上一个页面
    });


    // 监听分页链接的点击事件
    searchResultWrapper.addEventListener('click', function(event) {
        // 使用 event delegation 确保捕捉到分页链接的点击事件
        const target = event.target.closest('.page-link');
        if (target) {
            event.preventDefault();  // 阻止默认行为，防止页面刷新，通过 Ajax 获取新页面内容
            const page = target.getAttribute('data-page');  // 获取分页的页码
            if (page) {
                currentPage = parseInt(page);
                // 发起分页请求，获取下一页的结果
                fetchResults(query, currentPage);
            }
        }
    });

//    // 处理浏览器的前进和后退事件
//    window.addEventListener('popstate', function() {
//        const searchQuery = new URLSearchParams(window.location.search).get('q');
//        const page = new URLSearchParams(window.location.search).get('page') || 1;  // 检查 page 参数
//        if (searchQuery) {
//            fetchResults(searchQuery, '/search/?q=${encodeURIComponent(searchQuery)}&page=${page}', false);  // 使用 false 防止 URL 再次更新
//        }
//    });
});
