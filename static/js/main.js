// Global variables
let currentResults = null;
let currentPage = 1;
let resultsPerPage = 10;
let chart = null;

// DOM elements
const searchForm = document.getElementById('search-form');
const searchQuery = document.getElementById('search-query');
const sourceFilter = document.getElementById('source-filter');
const dateFromFilter = document.getElementById('date-from');
const dateToFilter = document.getElementById('date-to');
const sortByFilter = document.getElementById('sort-by');
const resultsPanel = document.getElementById('results-panel');
const searchLoader = document.getElementById('search-loader');
const resultsBody = document.getElementById('results-body');
const resultCount = document.getElementById('result-count');
const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const pageInfo = document.getElementById('page-info');
const vizPanel = document.getElementById('viz-panel');
const chartType = document.getElementById('chart-type');
const dataChart = document.getElementById('data-chart');

// Export buttons
const exportJson = document.getElementById('export-json');
const exportCsv = document.getElementById('export-csv');
const exportPdf = document.getElementById('export-pdf');

// Event listeners
searchForm.addEventListener('submit', handleSearch);
sourceFilter.addEventListener('change', applyFilters);
dateFromFilter.addEventListener('change', applyFilters);
dateToFilter.addEventListener('change', applyFilters);
sortByFilter.addEventListener('change', applySorting);
prevPageBtn.addEventListener('click', goToPrevPage);
nextPageBtn.addEventListener('click', goToNextPage);
chartType.addEventListener('change', updateVisualization);
exportJson.addEventListener('click', () => exportData('json'));
exportCsv.addEventListener('click', () => exportData('csv'));
exportPdf.addEventListener('click', () => exportData('pdf'));

// Search function
async function handleSearch(event) {
    event.preventDefault();
    
    const query = searchQuery.value.trim();
    if (!query) return;
    
    // Show loader, hide results
    searchLoader.classList.remove('hidden');
    resultsBody.innerHTML = '';
    
    try {
        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        
        // Get filters
        const filters = {
            source: sourceFilter.value,
            date_from: dateFromFilter.value,
            date_to: dateToFilter.value,
            sort_by: sortByFilter.value
        };
        
        // Make API request
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                query: query,
                filters: filters
            })
        });
        
        if (!response.ok) {
            throw new Error('Search request failed');
        }
        
        // Parse response
        currentResults = await response.json();
        currentPage = 1;
        
        // Display results
        displayResults();
        
        // Show results area
        resultsPanel.classList.remove('hidden');
        vizPanel.classList.remove('hidden');
        
        // Create visualization
        createVisualization();
        
    } catch (error) {
        console.error('Error during search:', error);
        resultsBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div style="padding: 2rem; text-align: center; color: var(--danger-color);">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>An error occurred while searching. Please try again.</p>
                    </div>
                </td>
            </tr>
        `;
    } finally {
        searchLoader.classList.add('hidden');
    }
}

// Display results function
function displayResults() {
    if (!currentResults || !currentResults.results || currentResults.results.length === 0) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div style="padding: 2rem; text-align: center; color: var(--gray-500);">
                        <i class="fas fa-search"></i>
                        <p>No results found. Try adjusting your search query or filters.</p>
                    </div>
                </td>
            </tr>
        `;
        resultCount.textContent = '(0)';
        updatePagination();
        return;
    }
    
    // Update result count
    resultCount.textContent = `(${currentResults.count})`;
    
    // Calculate pagination
    const startIndex = (currentPage - 1) * resultsPerPage;
    const endIndex = Math.min(startIndex + resultsPerPage, currentResults.results.length);
    const pageResults = currentResults.results.slice(startIndex, endIndex);
    
    // Clear previous results
    resultsBody.innerHTML = '';
    
    // Add results to table
    pageResults.forEach(result => {
        const relevanceClass = getRelevanceClass(result.relevance);
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.id}</td>
            <td><span class="badge ${getSourceClass(result.source)}">${result.source}</span></td>
            <td>${result.username}</td>
            <td>${truncateText(result.content, 50)}</td>
            <td>${result.date}</td>
            <td><div class="relevance-bar ${relevanceClass}" style="width: ${result.relevance * 100}%"></div> ${(result.relevance * 100).toFixed(1)}%</td>
            <td>
                <button class="action-btn" onclick="viewDetails(${result.id})"><i class="fas fa-eye"></i></button>
                <button class="action-btn" onclick="saveResult(${result.id})"><i class="fas fa-bookmark"></i></button>
            </td>
        `;
        resultsBody.appendChild(row);
    });
    
    // Update pagination
    updatePagination();
}

// Update pagination
function updatePagination() {
    if (!currentResults || !currentResults.results || currentResults.results.length === 0) {
        prevPageBtn.disabled = true;
        nextPageBtn.disabled = true;
        pageInfo.textContent = 'Page 0 of 0';
        return;
    }
    
    const totalPages = Math.ceil(currentResults.results.length / resultsPerPage);
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = currentPage === totalPages;
}

// Navigate to previous page
function goToPrevPage() {
    if (currentPage > 1) {
        currentPage--;
        displayResults();
        window.scrollTo(0, resultsPanel.offsetTop - 20);
    }
}

// Navigate to next page
function goToNextPage() {
    const totalPages = Math.ceil(currentResults.results.length / resultsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayResults();
        window.scrollTo(0, resultsPanel.offsetTop - 20);
    }
}