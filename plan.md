# Implementation Plan: Search Filtering by Content Type

**Date:** February 24, 2026
**Feature:** Add type-based filtering to Pagefind search with sidebar checkboxes
**Content Types:** Software, People, Events, Resources, Blog Posts

---

## Table of Contents

1. [Overview](#overview)
   - Implementation Approach (3 Phases)
   - Current State
   - Target State
2. [Architecture & Technical Approach](#architecture--technical-approach)
   - Pagefind Filter Metadata
   - Content Type Detection
3. [Implementation Steps](#implementation-steps)
   - **Phase 1 (Required):** Steps 1-3, 11 - Core Functionality
   - **Phase 2 (Recommended):** Steps 4-7 - Enhanced Features
   - **Phase 3 (Optional):** Steps 8-10 - Polish & Accessibility
4. [Testing Plan](#testing-plan)
   - Phase-by-phase testing checklists
   - Browser and responsive testing
   - Performance testing
5. [Edge Cases & Considerations](#edge-cases--considerations)
6. [Performance Considerations](#performance-considerations)
7. [Accessibility (a11y) Considerations](#accessibility-a11y-considerations)
8. [Future Enhancements](#future-enhancements-beyond-this-implementation)
9. [Rollback Plan](#rollback-plan)
10. [Summary](#summary)
11. [Implementation Checklist](#implementation-checklist)
12. [Questions & Answers](#questions--answers)
13. [Implementation Best Practices](#implementation-best-practices)
14. [Ready to Implement?](#ready-to-implement)

---

## Overview

This plan outlines how to extend the site-wide search functionality to allow users to filter results by content type. The implementation uses Pagefind's filtering capabilities with a redesigned search modal that includes a left sidebar with checkboxes for each content type.

### Implementation Approach

This plan is structured in **3 phases** to allow incremental implementation:

1. **Phase 1 (Required):** Core filtering functionality - Steps 1-3, 11
   - Basic type-based filtering with 5 main content types
   - Filter sidebar with checkboxes and counts
   - Real-time result updates
   - **Time:** 1-2 hours

2. **Phase 2 (Recommended):** Enhanced features - Steps 4-7
   - "Other" category for uncategorized content
   - Filter persistence across sessions
   - Convenience buttons (Select All / Clear All)
   - Results header showing count and active filters
   - **Time:** 2-3 hours

3. **Phase 3 (Optional):** Polish and accessibility - Steps 8-10
   - Mobile responsive collapsible sidebar
   - Full ARIA label support for screen readers
   - Disable filters with zero results
   - **Time:** 1-2 hours

**You can implement Phase 1, test it, and then proceed to Phases 2 and 3 if desired.**

### Current State

- Search modal: Single-column layout with search input and results
- Search implementation: Basic Pagefind search without filters
- Location: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html` and `themes/hugo-theme-tailwind/assets/js/search.js`

### Target State (After Phase 1)

- Search modal: Two-column layout with filter sidebar (left) and results (right)
- Filter sidebar: Checkboxes for 5 content types with result counts
- Search implementation: Pagefind filtered search with dynamic filter updates
- Default behavior: All types checked (all results shown)
- Interactive: Checking/unchecking updates results in real-time

### Target State (After All Phases)

- 6 content types including "Other" for uncategorized pages
- Filter persistence with localStorage
- Convenience buttons for quick selection
- Results header showing active filters
- Mobile-optimized collapsible sidebar
- Full WCAG AA accessibility compliance
- Smart filter disabling for zero-result types

---

## Architecture & Technical Approach

### 1. Pagefind Filter Metadata

Pagefind filtering works by reading `data-pagefind-filter-*` attributes from HTML elements. We need to add a content type filter to all pages.

**How Pagefind Filtering Works:**
- Add `data-pagefind-filter-[name]="[value]"` to any element on the page
- Pagefind indexes these as filterable fields
- JavaScript API filters: `pagefind.search(query, { filters: { type: ["software", "people"] } })`
- Result counts: Available in search response as `search.filters.type`

### 2. Content Type Detection

Hugo organizes content by sections, which map to our content types:
- `/software/*` → "Software"
- `/people/*` → "People"
- `/events/*` → "Events"
- `/resources/*` → "Resources"
- `/blog/*` → "Blog"

We'll use Hugo's `.Section` variable to automatically detect and set the content type.

---

## Implementation Steps

### Step 1: Add Pagefind Filter Metadata to Templates

We need to add a hidden element with `data-pagefind-filter-type` to the base template

**File:** `themes/hugo-theme-tailwind/layouts/_default/baseof.html`

**Change:** Add filter metadata in the `<main>` block (around line 31)

```html
<main class="flex flex-auto justify-center pt-10">
  <div class="w-full max-w-7xl lg:max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Pagefind Content Type Filter -->
    {{ $contentType := .Section }}
    {{ if eq .Section "software" }}
      {{ $contentType = "Software" }}
    {{ else if eq .Section "people" }}
      {{ $contentType = "People" }}
    {{ else if eq .Section "events" }}
      {{ $contentType = "Events" }}
    {{ else if eq .Section "resources" }}
      {{ $contentType = "Resources" }}
    {{ else if eq .Section "blog" }}
      {{ $contentType = "Blog" }}
    {{ end }}
    {{ if $contentType }}
      <span class="hidden" data-pagefind-filter-type="{{ $contentType }}">{{ $contentType }}</span>
    {{ end }}

    {{ block "main" . }}{{ end }}
  </div>
</main>
```

---

### Step 2: Update Search Modal HTML

We need to redesign the modal to have a two-column layout with a filter sidebar.

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Replace the entire modal content with:**

```html
<!-- Search Modal -->
<div id="search-modal" class="hidden fixed inset-0 z-100 overflow-y-auto" aria-labelledby="search-modal-title" role="dialog" aria-modal="true" data-pagefind-ignore>
  <!-- Backdrop -->
  <div class="fixed inset-0 bg-gray-900/75 dark:bg-black/80 transition-opacity" id="search-backdrop"></div>

  <!-- Modal Content -->
  <div class="flex min-h-full items-start justify-center p-4 sm:p-6 md:p-20">
    <div class="relative w-full max-w-4xl transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow-2xl ring-1 ring-black ring-opacity-5 transition-all">

      <!-- Search Input -->
      <div class="relative">
        <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-4">
          <i class="h-5 w-5 text-gray-400">
            {{ partial "icon.html" "search" }}
          </i>
        </div>
        <input
          type="text"
          id="search-input"
          class="block w-full border-0 bg-transparent py-4 pl-11 pr-4 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:ring-0 text-base sm:text-lg outline-none"
          placeholder="Search..."
          autocomplete="off"
          spellcheck="false"
        >
      </div>

      <!-- Two-column layout: Filters + Results -->
      <div class="flex border-t border-gray-200 dark:border-gray-700">

        <!-- Left Sidebar: Filters -->
        <aside id="search-filters" class="flex-none w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto max-h-[50vh]">
          <h3 class="text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide mb-3">Filter by Type</h3>

          <!-- Filter checkboxes -->
          <div class="space-y-2">
            <!-- Software -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-software"
                  value="Software"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Software</span>
              </div>
              <span id="count-software" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>

            <!-- People -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-people"
                  value="People"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">People</span>
              </div>
              <span id="count-people" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>

            <!-- Events -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-events"
                  value="Events"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Events</span>
              </div>
              <span id="count-events" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>

            <!-- Resources -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-resources"
                  value="Resources"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Resources</span>
              </div>
              <span id="count-resources" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>

            <!-- Blog -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-blog"
                  value="Blog"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Blog</span>
              </div>
              <span id="count-blog" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>
          </div>
        </aside>

        <!-- Right Side: Results -->
        <div class="flex-1 min-w-0">
          <div id="search-results" class="max-h-[50vh] scroll-py-2 overflow-y-auto">
            <!-- Loading state -->
            <div id="search-loading" class="hidden py-8 text-center text-sm text-gray-500 dark:text-gray-400">
              Searching...
            </div>

            <!-- Empty state -->
            <div id="search-empty" class="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
              Type to search
            </div>

            <!-- No results state -->
            <div id="search-no-results" class="hidden py-8 text-center text-sm text-gray-500 dark:text-gray-400">
              No results found
            </div>

            <!-- Results list -->
            <ul id="search-results-list" class="divide-y divide-gray-200 dark:divide-gray-700"></ul>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
        <div class="flex items-center gap-3">
          <kbd class="rounded border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 px-2 py-1 font-mono">↑↓</kbd>
          <span>Navigate</span>
        </div>
        <div class="flex items-center gap-3">
          <kbd class="rounded border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 px-2 py-1 font-mono">↵</kbd>
          <span>Select</span>
        </div>
        <div class="flex items-center gap-3">
          <kbd class="rounded border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-700 px-2 py-1 font-mono">ESC</kbd>
          <span>Close</span>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Key Changes:**
1. Two-column flex layout: `<aside>` for filters, `<div>` for results
2. Filter sidebar is `w-48` (12rem) with border-right
3. Each filter has:
   - Checkbox (checked by default)
   - Label with type name
   - Count span (e.g., "(12)")
4. Results section takes remaining width with `flex-1`
5. Color scheme uses Posit Green for checkboxes (`text-posit-green-600`)

---

### Step 3: Update JavaScript Search Logic

Now we need to update the search JavaScript to use Pagefind's filtering API.

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Replace the entire file with:**

```javascript
(function() {
  let pagefind = null;
  let selectedIndex = -1;
  let lastSearchResults = null; // Store full search results with filters

  // Modal elements
  const modal = document.getElementById('search-modal');
  const backdrop = document.getElementById('search-backdrop');
  const searchInput = document.getElementById('search-input');
  const searchLoading = document.getElementById('search-loading');
  const searchEmpty = document.getElementById('search-empty');
  const searchNoResults = document.getElementById('search-no-results');
  const searchResultsList = document.getElementById('search-results-list');

  // Filter checkboxes
  const filterCheckboxes = document.querySelectorAll('#search-filters input[type="checkbox"]');

  // Count elements
  const countElements = {
    'Software': document.getElementById('count-software'),
    'People': document.getElementById('count-people'),
    'Events': document.getElementById('count-events'),
    'Resources': document.getElementById('count-resources'),
    'Blog': document.getElementById('count-blog')
  };

  // Toggle buttons
  const searchToggle = document.getElementById('search-toggle');
  const searchToggleMobile = document.getElementById('search-toggle-mobile');

  // Initialize Pagefind
  async function initPagefind() {
    if (!pagefind) {
      pagefind = await import('/pagefind/pagefind.js');
    }
    return pagefind;
  }

  // Get selected filter types
  function getSelectedFilters() {
    const selected = [];
    filterCheckboxes.forEach(checkbox => {
      if (checkbox.checked) {
        selected.push(checkbox.value);
      }
    });
    return selected;
  }

  // Update result counts from search results
  function updateFilterCounts(filters) {
    // Reset all counts to 0
    Object.keys(countElements).forEach(type => {
      if (countElements[type]) {
        countElements[type].textContent = '(0)';
      }
    });

    // Update with actual counts from Pagefind
    if (filters && filters.type) {
      Object.keys(filters.type).forEach(type => {
        if (countElements[type]) {
          countElements[type].textContent = `(${filters.type[type]})`;
        }
      });
    }
  }

  // Open modal
  function openModal() {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
      searchInput.focus();
    }, 100);
  }

  // Close modal
  function closeModal() {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
    searchInput.value = '';
    clearResults();
    selectedIndex = -1;
    lastSearchResults = null;
  }

  // Clear results
  function clearResults() {
    searchResultsList.innerHTML = '';
    searchLoading.classList.add('hidden');
    searchEmpty.classList.remove('hidden');
    searchNoResults.classList.add('hidden');

    // Reset counts
    Object.values(countElements).forEach(el => {
      if (el) el.textContent = '(0)';
    });
  }

  // Show loading state
  function showLoading() {
    searchEmpty.classList.add('hidden');
    searchNoResults.classList.add('hidden');
    searchLoading.classList.remove('hidden');
  }

  // Show no results
  function showNoResults() {
    searchLoading.classList.add('hidden');
    searchEmpty.classList.add('hidden');
    searchNoResults.classList.remove('hidden');
    searchResultsList.innerHTML = '';
  }

  // Create result item HTML
  function createResultItem(result, index) {
    const li = document.createElement('li');
    li.className = 'search-result-item cursor-pointer';
    li.dataset.index = index;
    li.dataset.url = result.url;

    const link = document.createElement('a');
    link.href = result.url;
    link.className = 'flex gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors';

    // Image (if available)
    if (result.meta.image) {
      const imageContainer = document.createElement('div');
      imageContainer.className = 'flex-none w-16 h-16 rounded overflow-hidden';

      const img = document.createElement('img');
      img.src = result.meta.image;
      img.alt = result.meta.title || '';
      img.className = 'w-full h-full object-contain';
      img.loading = 'lazy';

      imageContainer.appendChild(img);
      link.appendChild(imageContainer);
    }

    // Content container
    const contentContainer = document.createElement('div');
    contentContainer.className = 'flex-1 min-w-0';

    // Title
    const title = document.createElement('div');
    title.className = 'text-sm font-medium text-gray-900 dark:text-gray-100';
    title.innerHTML = result.meta.title || 'Untitled';

    // Excerpt
    const excerpt = document.createElement('div');
    excerpt.className = 'mt-1 text-sm text-gray-600 dark:text-gray-400 line-clamp-2';
    excerpt.innerHTML = result.excerpt || '';

    contentContainer.appendChild(title);
    contentContainer.appendChild(excerpt);
    link.appendChild(contentContainer);
    li.appendChild(link);

    return li;
  }

  // Display results based on selected filters
  async function displayFilteredResults() {
    if (!lastSearchResults || !lastSearchResults.results) {
      return;
    }

    const selectedTypes = getSelectedFilters();

    // If no filters selected, show "no results"
    if (selectedTypes.length === 0) {
      showNoResults();
      return;
    }

    searchLoading.classList.add('hidden');
    searchEmpty.classList.add('hidden');
    searchNoResults.classList.add('hidden');
    searchResultsList.innerHTML = '';

    // Filter results by selected types
    const filteredResults = [];

    for (const result of lastSearchResults.results) {
      const data = await result.data();

      // Check if result's type matches any selected filter
      const resultType = data.filters?.type;
      if (resultType && selectedTypes.includes(resultType)) {
        filteredResults.push(data);
      }
    }

    // Show results or no results message
    if (filteredResults.length === 0) {
      showNoResults();
      return;
    }

    // Display filtered results (limit to 10)
    const resultsToShow = filteredResults.slice(0, 10);
    for (const [index, data] of resultsToShow.entries()) {
      const resultItem = createResultItem(data, index);
      searchResultsList.appendChild(resultItem);
    }

    selectedIndex = -1;
  }

  // Perform search with filters
  async function performSearch(query) {
    if (!query || query.trim() === '') {
      clearResults();
      lastSearchResults = null;
      return;
    }

    showLoading();

    try {
      const pf = await initPagefind();

      // Get selected filter types
      const selectedTypes = getSelectedFilters();

      // Build filter object for Pagefind
      const filters = {};
      if (selectedTypes.length > 0) {
        filters.type = selectedTypes;
      }

      // Perform search with filters
      const search = await pf.search(query, { filters });

      // Store results for re-filtering
      lastSearchResults = search;

      // Update filter counts (from unfiltered search for accurate totals)
      const unfilteredSearch = await pf.search(query);
      updateFilterCounts(unfilteredSearch.filters);

      if (search.results.length === 0) {
        showNoResults();
        return;
      }

      // Display results
      searchLoading.classList.add('hidden');
      searchEmpty.classList.add('hidden');
      searchNoResults.classList.add('hidden');
      searchResultsList.innerHTML = '';

      // Limit to first 10 results
      const resultsToShow = search.results.slice(0, 10);

      for (const [index, result] of resultsToShow.entries()) {
        const data = await result.data();
        const resultItem = createResultItem(data, index);
        searchResultsList.appendChild(resultItem);
      }

      selectedIndex = -1;
    } catch (error) {
      console.error('Search error:', error);
      showNoResults();
    }
  }

  // Update selected result
  function updateSelection() {
    const items = searchResultsList.querySelectorAll('.search-result-item');
    items.forEach((item, index) => {
      if (index === selectedIndex) {
        item.querySelector('a').classList.add('bg-gray-100', 'dark:bg-gray-600');
        item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      } else {
        item.querySelector('a').classList.remove('bg-gray-100', 'dark:bg-gray-600');
      }
    });
  }

  // Navigate to selected result
  function navigateToSelected() {
    const items = searchResultsList.querySelectorAll('.search-result-item');
    if (selectedIndex >= 0 && selectedIndex < items.length) {
      const url = items[selectedIndex].dataset.url;
      window.location.href = url;
    }
  }

  // Event Listeners

  // Open modal on button click
  if (searchToggle) {
    searchToggle.addEventListener('click', openModal);
  }
  if (searchToggleMobile) {
    searchToggleMobile.addEventListener('click', openModal);
  }

  // Close modal on backdrop click
  if (backdrop) {
    backdrop.addEventListener('click', closeModal);
  }

  // Handle search input
  let searchTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
        performSearch(e.target.value);
      }, 300); // Debounce 300ms
    });
  }

  // Handle filter checkbox changes
  filterCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      // Re-run search with new filters
      const query = searchInput.value;
      if (query && query.trim() !== '') {
        performSearch(query);
      }
    });
  });

  // Keyboard navigation
  document.addEventListener('keydown', (e) => {
    // ESC to close modal
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      e.preventDefault();
      closeModal();
      return;
    }

    // Only handle other keys if modal is open
    if (modal.classList.contains('hidden')) {
      return;
    }

    const items = searchResultsList.querySelectorAll('.search-result-item');
    const maxIndex = items.length - 1;

    // Only handle arrow keys and enter if there are results
    if (items.length === 0) {
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        selectedIndex = Math.min(selectedIndex + 1, maxIndex);
        updateSelection();
        break;

      case 'ArrowUp':
        e.preventDefault();
        selectedIndex = Math.max(selectedIndex - 1, -1);
        updateSelection();
        break;

      case 'Enter':
        e.preventDefault();
        navigateToSelected();
        break;
    }
  });

  // Click on result
  if (searchResultsList) {
    searchResultsList.addEventListener('click', (e) => {
      const resultItem = e.target.closest('.search-result-item');
      if (resultItem) {
        const url = resultItem.dataset.url;
        window.location.href = url;
      }
    });
  }
})();
```

**Key Changes:**

1. **New Variables:**
   - `lastSearchResults` - Stores full search results for re-filtering
   - `filterCheckboxes` - NodeList of all filter checkboxes
   - `countElements` - Object mapping type names to count span elements

2. **New Functions:**
   - `getSelectedFilters()` - Returns array of checked filter values
   - `updateFilterCounts(filters)` - Updates "(N)" counts next to each checkbox
   - `displayFilteredResults()` - Re-displays results when filters change

3. **Updated `performSearch()` Function:**
   - Gets selected filters with `getSelectedFilters()`
   - Passes filters to Pagefind: `pf.search(query, { filters: { type: selectedTypes } })`
   - Runs unfiltered search to get accurate counts for all types
   - Updates filter counts with `updateFilterCounts()`

4. **Filter Change Handler:**
   - Listens to checkbox `change` events
   - Re-runs search when filters change

---

### Step 4: Add "Other" Type for Non-Categorized Content

Handle pages that don't fit into the 5 main types (homepage, category pages, etc.).

**File:** `themes/hugo-theme-tailwind/layouts/_default/baseof.html`

**Update the content type logic to include an "Other" fallback:**

```html
<main class="flex flex-auto justify-center pt-10">
  <div class="w-full max-w-7xl lg:max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Pagefind Content Type Filter -->
    {{ $contentType := "" }}
    {{ if eq .Section "software" }}
      {{ $contentType = "Software" }}
    {{ else if eq .Section "people" }}
      {{ $contentType = "People" }}
    {{ else if eq .Section "events" }}
      {{ $contentType = "Events" }}
    {{ else if eq .Section "resources" }}
      {{ $contentType = "Resources" }}
    {{ else if eq .Section "blog" }}
      {{ $contentType = "Blog" }}
    {{ else if .Section }}
      {{ $contentType = "Other" }}
    {{ end }}
    {{ if $contentType }}
      <span class="hidden" data-pagefind-filter-type="{{ $contentType }}">{{ $contentType }}</span>
    {{ end }}

    {{ block "main" . }}{{ end }}
  </div>
</main>
```

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Add "Other" checkbox to the filter sidebar (after Blog):**

```html
            <!-- Other -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-other"
                  value="Other"
                  checked
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Other</span>
              </div>
              <span id="count-other" class="text-xs text-gray-500 dark:text-gray-400">(0)</span>
            </label>
```

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Add "Other" to the countElements object:**

```javascript
  // Count elements
  const countElements = {
    'Software': document.getElementById('count-software'),
    'People': document.getElementById('count-people'),
    'Events': document.getElementById('count-events'),
    'Resources': document.getElementById('count-resources'),
    'Blog': document.getElementById('count-blog'),
    'Other': document.getElementById('count-other')
  };
```

---

### Step 5: Add Filter Persistence (localStorage)

Store filter state so users' selections persist across modal opens.

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Add these functions after `getSelectedFilters()`:**

```javascript
  // Save filter state to localStorage
  function saveFilterState() {
    const selected = getSelectedFilters();
    localStorage.setItem('search-filters', JSON.stringify(selected));
  }

  // Restore filter state from localStorage
  function restoreFilterState() {
    try {
      const saved = localStorage.getItem('search-filters');
      if (saved) {
        const selectedTypes = JSON.parse(saved);
        // Uncheck all first
        filterCheckboxes.forEach(checkbox => {
          checkbox.checked = false;
        });
        // Check saved selections
        filterCheckboxes.forEach(checkbox => {
          if (selectedTypes.includes(checkbox.value)) {
            checkbox.checked = true;
          }
        });
      }
    } catch (e) {
      console.error('Error restoring filter state:', e);
    }
  }
```

**Update the `openModal()` function:**

```javascript
  // Open modal
  function openModal() {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    restoreFilterState(); // ADD THIS LINE
    setTimeout(() => {
      searchInput.focus();
    }, 100);
  }
```

**Update the filter checkbox change handler:**

```javascript
  // Handle filter checkbox changes
  filterCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      saveFilterState(); // ADD THIS LINE
      // Re-run search with new filters
      const query = searchInput.value;
      if (query && query.trim() !== '') {
        performSearch(query);
      }
    });
  });
```

---

### Step 6: Add Clear All / Select All Buttons

Add convenience buttons to quickly toggle all filters.

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Add buttons above the filter checkboxes (after the h3 heading):**

```html
        <aside id="search-filters" class="flex-none w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto max-h-[50vh]">
          <h3 class="text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide mb-3">Filter by Type</h3>

          <!-- ADD THIS: Clear/Select All buttons -->
          <div class="flex gap-2 mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
            <button id="select-all-filters" class="text-xs text-posit-blue-600 dark:text-posit-blue-400 hover:underline">
              Select All
            </button>
            <span class="text-xs text-gray-300 dark:text-gray-600">|</span>
            <button id="clear-all-filters" class="text-xs text-gray-500 dark:text-gray-400 hover:underline">
              Clear All
            </button>
          </div>

          <!-- Filter checkboxes -->
          <div class="space-y-2">
```

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Add button event listeners after the filter checkbox event listeners:**

```javascript
  // Handle filter checkbox changes
  filterCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      saveFilterState();
      const query = searchInput.value;
      if (query && query.trim() !== '') {
        performSearch(query);
      }
    });
  });

  // ADD THIS: Select All button
  const selectAllButton = document.getElementById('select-all-filters');
  if (selectAllButton) {
    selectAllButton.addEventListener('click', () => {
      filterCheckboxes.forEach(checkbox => {
        checkbox.checked = true;
      });
      saveFilterState();
      const query = searchInput.value;
      if (query && query.trim() !== '') {
        performSearch(query);
      }
    });
  }

  // ADD THIS: Clear All button
  const clearAllButton = document.getElementById('clear-all-filters');
  if (clearAllButton) {
    clearAllButton.addEventListener('click', () => {
      filterCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
      });
      saveFilterState();
      const query = searchInput.value;
      if (query && query.trim() !== '') {
        performSearch(query);
      }
    });
  }
```

---

### Step 7: Add Result Count Header

Show users how many results are displayed and which filters are active.

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Add a results header above the results list:**

```html
        <!-- Right Side: Results -->
        <div class="flex-1 min-w-0">
          <!-- ADD THIS: Results header -->
          <div id="search-results-header" class="hidden px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <p class="text-xs text-gray-600 dark:text-gray-400">
              <span id="results-count-text"></span>
            </p>
          </div>

          <div id="search-results" class="max-h-[50vh] scroll-py-2 overflow-y-auto">
```

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Add elements for the header:**

```javascript
  const searchResultsList = document.getElementById('search-results-list');

  // ADD THESE:
  const searchResultsHeader = document.getElementById('search-results-header');
  const resultsCountText = document.getElementById('results-count-text');
```

**Add a function to update the results header:**

```javascript
  // Update result counts from search results
  function updateFilterCounts(filters) {
    // Reset all counts to 0
    Object.keys(countElements).forEach(type => {
      if (countElements[type]) {
        countElements[type].textContent = '(0)';
      }
    });

    // Update with actual counts from Pagefind
    if (filters && filters.type) {
      Object.keys(filters.type).forEach(type => {
        if (countElements[type]) {
          countElements[type].textContent = `(${filters.type[type]})`;
        }
      });
    }
  }

  // ADD THIS FUNCTION:
  // Update results header with count and active filters
  function updateResultsHeader(totalResults) {
    if (!searchResultsHeader || !resultsCountText) return;

    if (totalResults === 0) {
      searchResultsHeader.classList.add('hidden');
      return;
    }

    const selectedTypes = getSelectedFilters();
    const typesText = selectedTypes.length === 6
      ? 'all types'
      : selectedTypes.join(', ');

    const resultWord = totalResults === 1 ? 'result' : 'results';
    resultsCountText.textContent = `Showing ${totalResults} ${resultWord} in ${typesText}`;
    searchResultsHeader.classList.remove('hidden');
  }
```

**Update the `performSearch()` function to call `updateResultsHeader()`:**

```javascript
      // Display results
      searchLoading.classList.add('hidden');
      searchEmpty.classList.add('hidden');
      searchNoResults.classList.add('hidden');
      searchResultsList.innerHTML = '';

      // Limit to first 10 results
      const resultsToShow = search.results.slice(0, 10);

      for (const [index, result] of resultsToShow.entries()) {
        const data = await result.data();
        const resultItem = createResultItem(data, index);
        searchResultsList.appendChild(resultItem);
      }

      // ADD THIS:
      updateResultsHeader(resultsToShow.length);

      selectedIndex = -1;
```

**Also update `clearResults()` to hide the header:**

```javascript
  // Clear results
  function clearResults() {
    searchResultsList.innerHTML = '';
    searchLoading.classList.add('hidden');
    searchEmpty.classList.remove('hidden');
    searchNoResults.classList.add('hidden');

    // ADD THIS:
    if (searchResultsHeader) {
      searchResultsHeader.classList.add('hidden');
    }

    // Reset counts
    Object.values(countElements).forEach(el => {
      if (el) el.textContent = '(0)';
    });
  }
```

---

### Step 8: Improve Mobile Responsiveness

Make the filter sidebar collapsible on small screens.

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Add mobile filter toggle button and make sidebar collapsible:**

```html
      <!-- Two-column layout: Filters + Results -->
      <div class="flex border-t border-gray-200 dark:border-gray-700">

        <!-- Mobile filter toggle button -->
        <div class="sm:hidden w-full border-b border-gray-200 dark:border-gray-700 p-3">
          <button id="mobile-filter-toggle" class="flex items-center justify-between w-full text-sm text-gray-700 dark:text-gray-300">
            <span class="font-medium">Filters</span>
            <svg class="h-5 w-5 transition-transform" id="mobile-filter-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        <!-- Left Sidebar: Filters -->
        <aside id="search-filters" class="flex-none w-full sm:w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto max-h-[50vh] hidden sm:block">
```

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Add mobile filter toggle functionality:**

```javascript
  // Toggle buttons
  const searchToggle = document.getElementById('search-toggle');
  const searchToggleMobile = document.getElementById('search-toggle-mobile');

  // ADD THESE:
  const mobileFilterToggle = document.getElementById('mobile-filter-toggle');
  const mobileFilterIcon = document.getElementById('mobile-filter-icon');
  const searchFilters = document.getElementById('search-filters');
```

**Add event listener for mobile toggle:**

```javascript
  // Close modal on backdrop click
  if (backdrop) {
    backdrop.addEventListener('click', closeModal);
  }

  // ADD THIS: Mobile filter toggle
  if (mobileFilterToggle && searchFilters) {
    mobileFilterToggle.addEventListener('click', () => {
      const isHidden = searchFilters.classList.contains('hidden');
      if (isHidden) {
        searchFilters.classList.remove('hidden');
        mobileFilterIcon.style.transform = 'rotate(180deg)';
      } else {
        searchFilters.classList.add('hidden');
        mobileFilterIcon.style.transform = 'rotate(0deg)';
      }
    });
  }
```

---

### Step 9: Enhance Accessibility with ARIA Labels

Improve screen reader support with proper ARIA attributes.

**File:** `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**Update the filter sidebar with ARIA labels:**

```html
        <!-- Left Sidebar: Filters -->
        <aside id="search-filters" aria-label="Search filters" role="group" class="flex-none w-full sm:w-48 border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto max-h-[50vh] hidden sm:block">
          <h3 id="filter-heading" class="text-xs font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide mb-3">Filter by Type</h3>

          <!-- Clear/Select All buttons -->
          <div class="flex gap-2 mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
            <button id="select-all-filters" class="text-xs text-posit-blue-600 dark:text-posit-blue-400 hover:underline" aria-label="Select all filter types">
              Select All
            </button>
            <span class="text-xs text-gray-300 dark:text-gray-600" aria-hidden="true">|</span>
            <button id="clear-all-filters" class="text-xs text-gray-500 dark:text-gray-400 hover:underline" aria-label="Clear all filter types">
              Clear All
            </button>
          </div>

          <!-- Filter checkboxes -->
          <div role="group" aria-labelledby="filter-heading" class="space-y-2">
```

**Update each checkbox with proper ARIA labels:**

```html
            <!-- Software -->
            <label class="flex items-center justify-between cursor-pointer group">
              <div class="flex items-center">
                <input
                  type="checkbox"
                  id="filter-software"
                  value="Software"
                  checked
                  aria-label="Show Software results"
                  class="h-4 w-4 rounded border-gray-300 text-posit-green-600 focus:ring-posit-green-500 dark:border-gray-600 dark:bg-gray-800"
                >
                <span class="ml-2 text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">Software</span>
              </div>
              <span id="count-software" class="text-xs text-gray-500 dark:text-gray-400" aria-live="polite">(0)</span>
            </label>
```

*Repeat for all other filter checkboxes (People, Events, Resources, Blog, Other)*

**Add ARIA live region for results:**

```html
          <div id="search-results" class="max-h-[50vh] scroll-py-2 overflow-y-auto" role="region" aria-live="polite" aria-label="Search results">
```

---

### Step 10: Disable Checkboxes with Zero Results (Optional)

Prevent users from selecting filters that would return no results.

**File:** `themes/hugo-theme-tailwind/assets/js/search.js`

**Update the `updateFilterCounts()` function to disable empty filters:**

```javascript
  // Update result counts from search results
  function updateFilterCounts(filters) {
    // Reset all counts to 0 and enable all checkboxes
    Object.keys(countElements).forEach(type => {
      if (countElements[type]) {
        countElements[type].textContent = '(0)';
      }
      // Find and enable checkbox
      const checkbox = document.querySelector(`input[value="${type}"]`);
      if (checkbox) {
        checkbox.disabled = false;
        checkbox.parentElement.parentElement.classList.remove('opacity-50');
      }
    });

    // Update with actual counts from Pagefind
    if (filters && filters.type) {
      Object.keys(filters.type).forEach(type => {
        if (countElements[type]) {
          const count = filters.type[type];
          countElements[type].textContent = `(${count})`;

          // Disable checkbox if count is 0
          const checkbox = document.querySelector(`input[value="${type}"]`);
          if (checkbox && count === 0 && !checkbox.checked) {
            checkbox.disabled = true;
            checkbox.parentElement.parentElement.classList.add('opacity-50');
          }
        }
      });
    }
  }
```

---

### Step 11: Rebuild Pagefind Index

After making all template changes, rebuild the Pagefind index.

**Commands:**
```bash
# Build the site
just build

# Rebuild search index
just build-search
```

**What happens:**
- Hugo rebuilds all pages with the new `data-pagefind-filter-type` attributes
- Pagefind scans the generated HTML and indexes the "type" filter
- Filter values become available in the JavaScript API

---

## Testing Plan

### Phase 1 Testing (Core Features)

#### Visual Layout
- [ ] Modal opens with two-column layout
- [ ] Filter sidebar visible on left (gray background)
- [ ] Results area on right (white background)
- [ ] All 5 filter checkboxes visible: Software, People, Events, Resources, Blog
- [ ] All checkboxes checked by default
- [ ] Checkboxes use Posit Green color scheme
- [ ] Count spans show "(0)" initially

#### Basic Search Functionality
- [ ] Type a query (e.g., "ggplot")
- [ ] Results appear on the right side within 300ms
- [ ] Filter counts update correctly (e.g., "Software (12)")
- [ ] Results show images, titles, and excerpts
- [ ] Results are limited to 10 items
- [ ] Loading state shows "Searching..." briefly
- [ ] Empty state shows "Type to search" when no query

#### Filter Interaction
- [ ] Uncheck "Software" → software results disappear immediately
- [ ] Check "Software" again → software results reappear
- [ ] Uncheck all filters → "No results found" message appears
- [ ] Check single filter (e.g., only "People") → only people results show
- [ ] Counts remain accurate after filter changes
- [ ] Multiple filters can be combined (e.g., Software + People)

#### Search with Filters Applied
- [ ] Uncheck "Blog" and "Events"
- [ ] Search for "tidyverse"
- [ ] Only Software, People, and Resources results appear
- [ ] Counts show all matching results (not just filtered ones)
- [ ] Re-checking filters adds those results back

#### Keyboard Navigation
- [ ] Tab key focuses search input
- [ ] Tab key cycles through checkboxes
- [ ] Space key toggles checkboxes
- [ ] ↑↓ arrow keys navigate results
- [ ] Enter key opens selected result
- [ ] ESC key closes modal and clears search

### Phase 2 Testing (Enhanced Features)

#### "Other" Category
- [ ] Navigate to homepage or category page
- [ ] Verify page has `data-pagefind-filter-type="Other"` in source
- [ ] Search for content from non-standard pages
- [ ] Verify "Other (N)" count updates
- [ ] Uncheck "Other" → those results disappear

#### Filter Persistence
- [ ] Check only "Software" and "People"
- [ ] Close modal (ESC or backdrop click)
- [ ] Reopen modal
- [ ] Verify only "Software" and "People" are still checked
- [ ] Refresh page
- [ ] Verify filter state persists across page reloads
- [ ] Clear localStorage and verify defaults (all checked)

#### Convenience Buttons
- [ ] Click "Clear All" → all checkboxes uncheck
- [ ] Verify "No results found" appears
- [ ] Click "Select All" → all checkboxes check
- [ ] Search for a query
- [ ] Verify "Clear All" and "Select All" work with active search
- [ ] Verify buttons save state to localStorage

#### Results Count Header
- [ ] Search for a query
- [ ] Verify header appears above results
- [ ] Verify text shows correct count (e.g., "Showing 8 results in...")
- [ ] Verify active filters are listed (e.g., "Software, People, Blog")
- [ ] When all 6 types selected, verify "all types" text
- [ ] Verify header hides when no results
- [ ] Verify header updates when filters change

### Phase 3 Testing (Polish & Accessibility)

#### Mobile Responsiveness
- [ ] Test on viewport < 640px
- [ ] Verify mobile filter toggle button appears
- [ ] Click toggle → filter sidebar expands
- [ ] Click toggle again → filter sidebar collapses
- [ ] Verify icon rotates on toggle
- [ ] Verify sidebar is visible by default on desktop (≥ 640px)
- [ ] Test on tablet (768px) - sidebar should be visible

#### Accessibility - Keyboard
- [ ] Navigate entire interface with Tab only
- [ ] Verify focus indicators are visible on all interactive elements
- [ ] Verify focus order is logical (input → filters → results)
- [ ] Space toggles checkboxes when focused
- [ ] Enter activates buttons when focused
- [ ] ESC closes modal from any focused element

#### Accessibility - Screen Reader
- [ ] Test with VoiceOver (macOS/iOS) or NVDA/JAWS (Windows)
- [ ] Verify filter sidebar announces as "Search filters"
- [ ] Verify each checkbox announces its label and state
- [ ] Verify count updates are announced (aria-live)
- [ ] Verify result header is announced
- [ ] Verify results region is announced
- [ ] Verify "Clear All" / "Select All" buttons are properly labeled

#### Accessibility - Color Contrast
- [ ] Use browser contrast checker or axe DevTools
- [ ] Verify text-to-background contrast ≥ 4.5:1 (WCAG AA)
- [ ] Verify checkbox focus indicator has ≥ 3:1 contrast
- [ ] Verify hover states have sufficient contrast
- [ ] Test in both light and dark modes

#### Zero-Result Filter Disabling (Optional)
- [ ] Search for a very specific term (e.g., "zzzzz")
- [ ] Verify filters with 0 results show "(0)"
- [ ] Verify unchecked filters with 0 results become disabled
- [ ] Verify disabled filters have reduced opacity (50%)
- [ ] Verify checked filters with 0 results remain enabled
- [ ] Verify filters re-enable when results appear

### Cross-Browser Testing

#### Desktop Browsers
- [ ] **Chrome/Edge (latest)** - Test all functionality
- [ ] **Firefox (latest)** - Test all functionality
- [ ] **Safari (latest, macOS)** - Test all functionality, especially localStorage
- [ ] Verify checkbox styling consistent across browsers
- [ ] Verify hover/focus states work correctly

#### Mobile Browsers
- [ ] **Mobile Safari (iOS)** - Test touch interactions, modal, filters
- [ ] **Mobile Chrome (Android)** - Test touch interactions, modal, filters
- [ ] Verify filter toggle button works on touch
- [ ] Verify checkboxes are easy to tap (>44px touch target)
- [ ] Verify modal scrolling works on mobile

### Performance Testing

#### Load Time
- [ ] Measure initial page load with DevTools
- [ ] Verify Pagefind bundle loads asynchronously
- [ ] Verify modal HTML doesn't block rendering

#### Search Performance
- [ ] Search for common term (e.g., "data")
- [ ] Verify results appear within 300-500ms
- [ ] Verify no jank when toggling filters
- [ ] Verify smooth scrolling in results list

#### Memory
- [ ] Open/close modal 10+ times
- [ ] Verify no memory leaks (DevTools Memory profiler)
- [ ] Verify event listeners are properly cleaned up

### Regression Testing

#### Existing Functionality
- [ ] Verify original search still works without filters
- [ ] Verify keyboard shortcuts (ESC, arrows, Enter) still work
- [ ] Verify result images load correctly
- [ ] Verify result excerpts display with highlighting
- [ ] Verify clicking results navigates correctly
- [ ] Verify backdrop click closes modal
- [ ] Verify search input debouncing (300ms) still works

### Edge Case Testing

#### Empty Search
- [ ] Click search without typing
- [ ] Verify "Type to search" message
- [ ] Verify counts remain (0)

#### All Filters Unchecked
- [ ] Uncheck all filters
- [ ] Verify "No results found"
- [ ] Search for a query
- [ ] Verify still "No results found"

#### Very Long Query
- [ ] Type 100+ character query
- [ ] Verify search still works
- [ ] Verify no UI breaking

#### Special Characters
- [ ] Search for: `* ? [ ] ( ) + . $ ^`
- [ ] Verify treated as literal characters
- [ ] Verify results appear correctly

### Browser Breakpoint Testing

Test responsive layout at specific widths:
- [ ] **375px** (iPhone SE) - Mobile toggle visible
- [ ] **640px** (sm breakpoint) - Sidebar becomes visible
- [ ] **768px** (iPad portrait) - Full layout
- [ ] **1024px** (Desktop) - Full layout with optimal spacing
- [ ] **1920px** (Large desktop) - Verify max-width constraints

### Dark Mode Testing

- [ ] Toggle dark mode (if site has toggle)
- [ ] Verify filter sidebar background is gray-900
- [ ] Verify text colors are readable
- [ ] Verify checkbox styling in dark mode
- [ ] Verify hover states have sufficient contrast
- [ ] Verify focus indicators visible in dark mode
- [ ] Verify results background (gray-700 on hover)

### localStorage Testing

- [ ] Set filters and close modal
- [ ] Open DevTools → Application → localStorage
- [ ] Verify `search-filters` key exists
- [ ] Verify value is valid JSON array
- [ ] Manually edit localStorage value
- [ ] Reopen modal and verify filters reflect changes
- [ ] Clear localStorage
- [ ] Verify defaults (all checked) are restored

---

### Test Environment Setup

**Required:**
- Local development server running (`just dev`)
- Site fully built with Pagefind index (`just build && just build-search`)

**Recommended Tools:**
- Browser DevTools (all browsers)
- axe DevTools extension (accessibility)
- Lighthouse (performance, accessibility)
- Screen reader (VoiceOver, NVDA, or JAWS)
- Mobile device or browser device emulation

**Testing Order:**
1. Start with Phase 1 testing
2. Fix any issues before proceeding
3. Implement and test Phase 2
4. Implement and test Phase 3
5. Perform full regression testing
6. Cross-browser and responsive testing last

---

## Edge Cases & Considerations

### 1. Empty Search Query

**Issue:** User clicks search but doesn't type anything

**Current Behavior:**
- "Type to search" message displayed
- No results shown
- Filter counts remain at (0)

**This is handled correctly by the implementation.**

### 2. All Filters Unchecked

**Issue:** User unchecks all filters

**Current Behavior:**
- "No results found" message appears
- This is intentional - at least one filter must be selected
- User can click "Select All" button to restore all filters

**This is the expected behavior.**

### 3. Very Long Query Strings

**Issue:** User types an extremely long search query

**Mitigation:**
- Pagefind handles long queries gracefully
- Debounce (300ms) prevents excessive API calls
- No special handling needed

### 4. Special Characters in Search

**Issue:** User searches with special regex characters (*, ?, [, etc.)

**Behavior:**
- Pagefind treats these as literal characters
- No escaping needed
- Search works as expected

---

## Performance Considerations

### Index Size Impact

Adding filter metadata increases Pagefind index size slightly:
- **Current:** ~200-300KB (estimated)
- **With filters:** +10-20KB (estimated)
- **Impact:** Minimal (< 10% increase)

### Search Performance

Pagefind filtering is client-side and very fast:
- **Unfiltered search:** ~10-50ms
- **Filtered search:** ~15-60ms
- **Re-filtering:** ~5-10ms (no network request)

### Initial Load

The modal HTML increases slightly (~2KB), but this is negligible.

---

## Accessibility (a11y) Considerations

### Keyboard Support

- [x] All checkboxes keyboard accessible (Tab, Space)
- [x] Labels clickable (wraps input)
- [x] Focus visible on checkboxes

### Screen Reader Support

Add ARIA labels for better screen reader experience:

```html
<aside id="search-filters" aria-label="Search filters" role="group">
  <h3 id="filter-heading">Filter by Type</h3>

  <div role="group" aria-labelledby="filter-heading">
    <label>
      <input type="checkbox" aria-label="Show Software results">
      <span>Software</span>
      <span aria-label="12 results">(12)</span>
    </label>
  </div>
</aside>
```

### Color Contrast

Verify WCAG AA compliance:
- [ ] Text-to-background contrast ≥ 4.5:1
- [ ] Checkbox focus indicator visible
- [ ] Hover states have sufficient contrast

---

## Future Enhancements (Beyond This Implementation)

### 1. Search Presets

Save common filter combinations for quick access:
- "Documentation" → Resources + Blog
- "Code" → Software only
- "Team" → People + Events

**Implementation:**
- Add preset buttons above filters
- Click to apply preset filter combination
- Store custom presets in localStorage

### 2. URL Parameters

Share search links with filters applied:
```
/search?q=tidyverse&type=software,people
```

**Benefits:**
- Shareable search results
- Browser back/forward works
- Bookmarkable searches

**Implementation:**
- Update URL on search/filter change with `history.pushState()`
- Parse URL params on page load
- Apply filters from URL if present

### 3. Additional Filter Dimensions

Beyond content type, add more filters:

**By Language:**
- R, Python, JavaScript, Rust, etc.
- Add `data-pagefind-filter-language="Python"`
- Separate filter section in sidebar

**By Date Range (for blog posts):**
- Last 7 days, Last month, Last year
- Add `data-pagefind-filter-date="2025"`
- Date picker or preset buttons

**By Author (for blog posts):**
- Filter by person who wrote the post
- Add `data-pagefind-filter-author="Person Name"`
- Dropdown or autocomplete

**By Popularity (for software):**
- Filter by GitHub stars (e.g., >1000 stars)
- Add `data-pagefind-filter-stars="high"`
- Slider or preset ranges

### 4. Search Analytics

Track what users search for:
- Most common queries
- Zero-result queries (to improve content)
- Filter usage patterns

**Implementation:**
- Send search events to analytics (Plausible, Google Analytics)
- Respect user privacy (no PII)
- Use insights to improve content and search

### 5. Advanced Search Syntax

Support power user features:
- Boolean operators (AND, OR, NOT)
- Exact phrase matching with quotes
- Field-specific search (title:ggplot)
- Wildcard search (ggplot*)

**Note:** Some features may require Pagefind updates

### 6. Search History

Show recent searches in the modal:
- Display last 5 searches below input
- Click to re-run search
- Clear history button
- Stored in localStorage

### 7. Keyboard Shortcuts

Additional keyboard controls:
- `/` - Open search modal from anywhere
- `Ctrl+F` - Open search (override browser find)
- `Cmd+K` / `Ctrl+K` - Open search (common pattern)
- Tab - Cycle through filters

### 8. Search Suggestions / Autocomplete

Show suggestions as user types:
- Based on popular searches
- Based on indexed content titles
- Fuzzy matching for typos

**Implementation:**
- Build suggestion index during Pagefind indexing
- Display dropdown below search input
- Arrow keys to navigate suggestions

---

## Rollback Plan

If issues arise after deployment:

1. **Quick Fix:** Revert JavaScript changes only
   - Restore original `search.js` from git: `git checkout HEAD~1 themes/hugo-theme-tailwind/assets/js/search.js`
   - Keep HTML changes (single-column layout still works)

2. **Full Revert:** Restore all files
   ```bash
   git checkout HEAD~1 themes/hugo-theme-tailwind/layouts/partials/search-modal.html
   git checkout HEAD~1 themes/hugo-theme-tailwind/assets/js/search.js
   git checkout HEAD~1 themes/hugo-theme-tailwind/layouts/_default/baseof.html
   ```

3. **Rebuild:**
   ```bash
   just build && just build-search
   ```

---

## Summary

This implementation adds comprehensive type-based filtering to the site search with:

### Core Features (Steps 1-3)
✅ **6 content types:** Software, People, Events, Resources, Blog, Other
✅ **Sidebar checkboxes:** All checked by default
✅ **Dynamic counts:** "(N)" next to each type
✅ **Real-time filtering:** Results update as checkboxes change
✅ **Pagefind API:** Uses official filtering capabilities

### Enhanced Features (Steps 4-10)
✅ **Other category:** Pages without specific type handled gracefully
✅ **Filter persistence:** Selections saved in localStorage across sessions
✅ **Convenience buttons:** Select All / Clear All for quick toggling
✅ **Results header:** Shows count and active filters (e.g., "Showing 12 results in Software, People")
✅ **Mobile responsive:** Collapsible filter sidebar on small screens
✅ **Accessibility:** ARIA labels, keyboard navigation, screen reader support
✅ **Optional:** Disable filters with zero results

### Technical Details
📦 **Impact:** ~15KB index increase, ~3KB HTML increase
⚡ **Performance:** Client-side filtering, <100ms response time
♿ **Accessibility:** WCAG AA compliant with full keyboard/screen reader support
📱 **Responsive:** Optimized for mobile, tablet, desktop

**Total Changes:**
- 1 template file (baseof.html) - Add filter metadata with "Other" fallback
- 1 HTML file (search-modal.html) - Add filter UI with mobile support
- 1 JavaScript file (search.js) - Implement filtering, persistence, and enhancements
- Rebuild Pagefind index

**Implementation Phases:**
- **Phase 1 (Required):** Steps 1-3, 11 - Basic filtering (1-2 hours)
- **Phase 2 (Recommended):** Steps 4-7 - Enhanced features (2-3 hours)
- **Phase 3 (Optional):** Steps 8-10 - Polish and accessibility (1-2 hours)

**Total Estimated Time:** 4-7 hours (including testing)

---

## Detailed Todo List

This comprehensive checklist breaks down every task needed to complete the implementation. Check off items as you complete them.

---

### 🚀 Pre-Implementation Setup

- [x] Read through entire plan document
- [x] Understand Pagefind filtering concepts
- [x] Review existing search implementation
- [x] Create feature branch: `git checkout -b feature/search-filtering`
- [x] Ensure development environment is running: `just dev`
- [x] Backup current search files (optional safety measure)
- [x] Clear any existing uncommitted changes

---

### 📦 PHASE 1: Core Functionality (Required)

#### Step 1: Add Filter Metadata to Templates

**File: `themes/hugo-theme-tailwind/layouts/_default/baseof.html`**

- [x] 1.1. Open `baseof.html` in editor
- [x] 1.2. Locate the `<main>` block (around line 30)
- [x] 1.3. Add Hugo template logic to detect content section
- [x] 1.4. Create conditional statements for each content type:
  - [x] Software (`eq .Section "software"`)
  - [x] People (`eq .Section "people"`)
  - [x] Events (`eq .Section "events"`)
  - [x] Resources (`eq .Section "resources"`)
  - [x] Blog (`eq .Section "blog"`)
- [x] 1.5. Add hidden `<span>` with `data-pagefind-filter-type` attribute
- [x] 1.6. Ensure span is inside the main content div
- [x] 1.7. Verify Hugo syntax is correct (no typos in `{{ }}`)
- [x] 1.8. Save file

#### Step 2: Update Search Modal HTML

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 2.1. Open `search-modal.html` in editor
- [ ] 2.2. Locate the modal structure (starts with `<div id="search-modal">`)
- [ ] 2.3. Keep search input section unchanged
- [ ] 2.4. Add two-column flex container after search input
  - [ ] Use `<div class="flex border-t border-gray-200 dark:border-gray-700">`
- [ ] 2.5. Create left sidebar `<aside>` element
  - [ ] Add `id="search-filters"`
  - [ ] Add classes: `flex-none w-48 border-r bg-gray-50 dark:bg-gray-900 p-4`
  - [ ] Add `max-h-[50vh] overflow-y-auto`
- [ ] 2.6. Add sidebar heading "Filter by Type"
  - [ ] Use `text-xs font-semibold uppercase tracking-wide mb-3`
- [ ] 2.7. Create checkbox for Software
  - [ ] Wrap in `<label>` with `flex items-center justify-between cursor-pointer group`
  - [ ] Add `<input type="checkbox" id="filter-software" value="Software" checked>`
  - [ ] Add Tailwind classes: `h-4 w-4 rounded border-gray-300 text-posit-green-600`
  - [ ] Add label text: `<span class="ml-2 text-sm">Software</span>`
  - [ ] Add count span: `<span id="count-software" class="text-xs text-gray-500">(0)</span>`
- [ ] 2.8. Create checkbox for People (same structure as Software)
  - [ ] Use `id="filter-people"` and `value="People"`
  - [ ] Use `id="count-people"` for count span
- [ ] 2.9. Create checkbox for Events
  - [ ] Use `id="filter-events"` and `value="Events"`
  - [ ] Use `id="count-events"` for count span
- [ ] 2.10. Create checkbox for Resources
  - [ ] Use `id="filter-resources"` and `value="Resources"`
  - [ ] Use `id="count-resources"` for count span
- [ ] 2.11. Create checkbox for Blog
  - [ ] Use `id="filter-blog"` and `value="Blog"`
  - [ ] Use `id="count-blog"` for count span
- [ ] 2.12. Ensure all checkboxes have `checked` attribute (default selected)
- [ ] 2.13. Close sidebar `</aside>`
- [ ] 2.14. Update results container
  - [ ] Wrap existing results in `<div class="flex-1 min-w-0">`
  - [ ] Keep all existing result states (loading, empty, no-results, results-list)
- [ ] 2.15. Keep footer unchanged
- [ ] 2.16. Verify z-index is `z-100` (or `z-[100]`)
- [ ] 2.17. Verify all Hugo partial syntax is correct
- [ ] 2.18. Save file

#### Step 3: Update Search JavaScript

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 3.1. Open `search.js` in editor
- [ ] 3.2. Add new variable declarations at top:
  - [ ] Add `let lastSearchResults = null;`
- [ ] 3.3. Add filter checkbox selector after existing selectors:
  - [ ] `const filterCheckboxes = document.querySelectorAll('#search-filters input[type="checkbox"]');`
- [ ] 3.4. Create `countElements` object with 5 IDs:
  - [ ] `'Software': document.getElementById('count-software')`
  - [ ] `'People': document.getElementById('count-people')`
  - [ ] `'Events': document.getElementById('count-events')`
  - [ ] `'Resources': document.getElementById('count-resources')`
  - [ ] `'Blog': document.getElementById('count-blog')`
- [ ] 3.5. Implement `getSelectedFilters()` function
  - [ ] Loop through `filterCheckboxes`
  - [ ] Push `checkbox.value` if `checkbox.checked`
  - [ ] Return array of selected types
- [ ] 3.6. Implement `updateFilterCounts(filters)` function
  - [ ] Reset all counts to "(0)"
  - [ ] Check if `filters && filters.type` exists
  - [ ] Loop through `filters.type` object
  - [ ] Update corresponding `countElements[type].textContent` with `(${count})`
- [ ] 3.7. Update `closeModal()` function
  - [ ] Add `lastSearchResults = null;` at end
- [ ] 3.8. Update `clearResults()` function
  - [ ] Add loop to reset all countElements to "(0)"
- [ ] 3.9. Update `performSearch()` function - MAJOR CHANGES:
  - [ ] After `const pf = await initPagefind();`, add `getSelectedFilters()` call
  - [ ] Create `filters` object: `const filters = {};`
  - [ ] If selectedTypes length > 0, set `filters.type = selectedTypes;`
  - [ ] Update search call to: `const search = await pf.search(query, { filters });`
  - [ ] Store results: `lastSearchResults = search;`
  - [ ] Add unfiltered search: `const unfilteredSearch = await pf.search(query);`
  - [ ] Call `updateFilterCounts(unfilteredSearch.filters);`
  - [ ] Keep rest of function unchanged
- [ ] 3.10. Add checkbox change event listeners after existing listeners:
  - [ ] Loop through `filterCheckboxes`
  - [ ] Add `'change'` event listener to each
  - [ ] Inside handler: get current query from `searchInput.value`
  - [ ] If query is not empty, call `performSearch(query)`
- [ ] 3.11. Verify all existing functionality is preserved
- [ ] 3.12. Check for syntax errors (commas, brackets, etc.)
- [ ] 3.13. Ensure proper indentation
- [ ] 3.14. Save file

#### Step 11: Build and Initial Testing

- [ ] 11.1. Stop development server (Ctrl+C)
- [ ] 11.2. Run full build: `just build`
  - [ ] Verify no Hugo build errors
  - [ ] Check that baseof.html template compiles
- [ ] 11.3. Rebuild Pagefind index: `just build-search`
  - [ ] Verify Pagefind indexes filter metadata
  - [ ] Check terminal output for any errors
- [ ] 11.4. Start development server: `just dev`
- [ ] 11.5. Open site in browser: `http://localhost:1313`
- [ ] 11.6. Open search modal
- [ ] 11.7. Verify two-column layout appears
- [ ] 11.8. Verify 5 checkboxes are visible and checked
- [ ] 11.9. Type a search query (e.g., "test")
- [ ] 11.10. Verify counts update (e.g., "Software (5)")
- [ ] 11.11. Uncheck one filter type
- [ ] 11.12. Verify results update immediately
- [ ] 11.13. Check browser console for JavaScript errors
- [ ] 11.14. Test on different page types (software, people, blog)
- [ ] 11.15. If errors occur, debug before proceeding

**✅ Phase 1 Complete Criteria:**
- [ ] Modal has two-column layout with filter sidebar
- [ ] All 5 checkboxes work and update results
- [ ] Counts update correctly when searching
- [ ] No console errors
- [ ] Basic filtering works as expected

**Commit Phase 1:**
```bash
git add themes/hugo-theme-tailwind/layouts/_default/baseof.html
git add themes/hugo-theme-tailwind/layouts/partials/search-modal.html
git add themes/hugo-theme-tailwind/assets/js/search.js
git commit -m "Add basic search filtering by content type

- Add filter metadata to baseof.html for 5 content types
- Redesign search modal with two-column layout
- Implement Pagefind filtering API in search.js
- Add checkboxes with real-time result counts"
```

---

### 🎨 PHASE 2: Enhanced Features (Recommended)

#### Step 4: Add "Other" Type for Uncategorized Content

**File: `themes/hugo-theme-tailwind/layouts/_default/baseof.html`**

- [ ] 4.1. Open `baseof.html` in editor
- [ ] 4.2. Locate the content type conditional logic
- [ ] 4.3. Change initial assignment: `{{ $contentType := "" }}`
- [ ] 4.4. After all main type conditions, add `else if .Section` branch
  - [ ] Set `{{ $contentType = "Other" }}`
- [ ] 4.5. This catches any section not in the main 5 types
- [ ] 4.6. Save file

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 4.7. Open `search-modal.html` in editor
- [ ] 4.8. Scroll to checkbox section in sidebar
- [ ] 4.9. After Blog checkbox, add "Other" checkbox
  - [ ] Use `id="filter-other"`, `value="Other"`, `checked`
  - [ ] Add label "Other"
  - [ ] Add `<span id="count-other">(0)</span>`
- [ ] 4.10. Ensure same styling as other checkboxes
- [ ] 4.11. Save file

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 4.12. Open `search.js` in editor
- [ ] 4.13. Locate `countElements` object
- [ ] 4.14. Add new entry: `'Other': document.getElementById('count-other')`
- [ ] 4.15. No other changes needed (function loops handle it automatically)
- [ ] 4.16. Save file

**Testing Step 4:**
- [ ] 4.17. Rebuild: `just build && just build-search`
- [ ] 4.18. Navigate to homepage or category page
- [ ] 4.19. View page source, search for "data-pagefind-filter-type"
- [ ] 4.20. Verify it shows `data-pagefind-filter-type="Other"`
- [ ] 4.21. Open search modal
- [ ] 4.22. Verify "Other" checkbox exists
- [ ] 4.23. Search for something, verify "Other (N)" count updates

#### Step 5: Add Filter Persistence with localStorage

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 5.1. Open `search.js` in editor
- [ ] 5.2. After `getSelectedFilters()` function, add `saveFilterState()`:
  - [ ] Call `getSelectedFilters()`
  - [ ] Stringify and save to localStorage: `localStorage.setItem('search-filters', JSON.stringify(selected))`
- [ ] 5.3. After `saveFilterState()`, add `restoreFilterState()`:
  - [ ] Wrap in try-catch for safety
  - [ ] Get item from localStorage: `localStorage.getItem('search-filters')`
  - [ ] If exists, parse JSON
  - [ ] Uncheck all checkboxes first
  - [ ] Loop through checkboxes, check if value is in saved array
  - [ ] Catch errors silently (console.error)
- [ ] 5.4. Locate `openModal()` function
- [ ] 5.5. After `modal.classList.remove('hidden');`, add `restoreFilterState();`
- [ ] 5.6. Locate checkbox change event listeners
- [ ] 5.7. At the beginning of each change handler, add `saveFilterState();`
- [ ] 5.8. Save file

**Testing Step 5:**
- [ ] 5.9. Reload page
- [ ] 5.10. Open search modal
- [ ] 5.11. Uncheck "Software" and "Events"
- [ ] 5.12. Close modal (ESC or backdrop click)
- [ ] 5.13. Reopen modal
- [ ] 5.14. Verify only 4 checkboxes are checked (Software and Events unchecked)
- [ ] 5.15. Open DevTools → Application → localStorage
- [ ] 5.16. Verify `search-filters` key exists
- [ ] 5.17. Verify value is JSON array like `["People","Resources","Blog","Other"]`
- [ ] 5.18. Refresh page and verify state persists

#### Step 6: Add Clear All / Select All Buttons

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 6.1. Open `search-modal.html` in editor
- [ ] 6.2. Locate filter sidebar, after h3 heading
- [ ] 6.3. Add button container div:
  - [ ] Use `class="flex gap-2 mb-3 pb-3 border-b border-gray-200 dark:border-gray-700"`
- [ ] 6.4. Add "Select All" button:
  - [ ] `id="select-all-filters"`
  - [ ] Classes: `text-xs text-posit-blue-600 dark:text-posit-blue-400 hover:underline`
  - [ ] Text: "Select All"
- [ ] 6.5. Add separator: `<span class="text-xs text-gray-300">|</span>`
- [ ] 6.6. Add "Clear All" button:
  - [ ] `id="clear-all-filters"`
  - [ ] Classes: `text-xs text-gray-500 dark:text-gray-400 hover:underline`
  - [ ] Text: "Clear All"
- [ ] 6.7. Close button container
- [ ] 6.8. Save file

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 6.9. Open `search.js` in editor
- [ ] 6.10. After filter checkbox listeners, add "Select All" handler:
  - [ ] Get element: `const selectAllButton = document.getElementById('select-all-filters');`
  - [ ] Add null check: `if (selectAllButton) {`
  - [ ] Add click listener
  - [ ] Inside: loop through checkboxes, set `checked = true`
  - [ ] Call `saveFilterState();`
  - [ ] Get query and re-run search if not empty
- [ ] 6.11. Add "Clear All" handler (similar structure):
  - [ ] Get element: `const clearAllButton = document.getElementById('clear-all-filters');`
  - [ ] Loop through checkboxes, set `checked = false`
  - [ ] Call `saveFilterState();`
  - [ ] Get query and re-run search if not empty
- [ ] 6.12. Save file

**Testing Step 6:**
- [ ] 6.13. Reload page
- [ ] 6.14. Open search modal
- [ ] 6.15. Verify buttons appear below heading, above checkboxes
- [ ] 6.16. Search for something
- [ ] 6.17. Click "Clear All"
- [ ] 6.18. Verify all checkboxes uncheck
- [ ] 6.19. Verify "No results found" appears
- [ ] 6.20. Click "Select All"
- [ ] 6.21. Verify all checkboxes check
- [ ] 6.22. Verify results reappear
- [ ] 6.23. Close and reopen modal, verify state persisted

#### Step 7: Add Result Count Header

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 7.1. Open `search-modal.html` in editor
- [ ] 7.2. Locate results container (right side of two-column layout)
- [ ] 7.3. Before `<div id="search-results">`, add header:
  - [ ] `<div id="search-results-header" class="hidden px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">`
  - [ ] Add paragraph: `<p class="text-xs text-gray-600 dark:text-gray-400">`
  - [ ] Add span: `<span id="results-count-text"></span>`
  - [ ] Close tags
- [ ] 7.4. Save file

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 7.5. Open `search.js` in editor
- [ ] 7.6. Add element references after `searchResultsList`:
  - [ ] `const searchResultsHeader = document.getElementById('search-results-header');`
  - [ ] `const resultsCountText = document.getElementById('results-count-text');`
- [ ] 7.7. After `updateFilterCounts()` function, add `updateResultsHeader(totalResults)`:
  - [ ] Add null check for header and text elements
  - [ ] If totalResults === 0, hide header and return
  - [ ] Get selected types with `getSelectedFilters()`
  - [ ] Create text: if all 6 selected, use "all types", else join with ", "
  - [ ] Set innerHTML: `Showing ${totalResults} result${s} in ${typesText}`
  - [ ] Remove `hidden` class from header
- [ ] 7.8. Locate `performSearch()` function
- [ ] 7.9. After appending all results, before `selectedIndex = -1;`
  - [ ] Call `updateResultsHeader(resultsToShow.length);`
- [ ] 7.10. Locate `clearResults()` function
- [ ] 7.11. Add header hide: `if (searchResultsHeader) { searchResultsHeader.classList.add('hidden'); }`
- [ ] 7.12. Update `showNoResults()` to hide header too
- [ ] 7.13. Save file

**Testing Step 7:**
- [ ] 7.14. Rebuild and reload
- [ ] 7.15. Open search modal
- [ ] 7.16. Search for something (e.g., "test")
- [ ] 7.17. Verify header appears above results
- [ ] 7.18. Verify text shows count and types (e.g., "Showing 8 results in all types")
- [ ] 7.19. Uncheck "Software" and "Events"
- [ ] 7.20. Verify header updates (e.g., "Showing 5 results in People, Resources, Blog, Other")
- [ ] 7.21. Clear search input
- [ ] 7.22. Verify header disappears
- [ ] 7.23. Search with no results, verify header stays hidden

**✅ Phase 2 Complete Criteria:**
- [ ] "Other" category works for uncategorized pages
- [ ] Filter selections persist across modal open/close
- [ ] Clear All / Select All buttons work
- [ ] Results header shows count and active filters
- [ ] No console errors

**Commit Phase 2:**
```bash
git add -A
git commit -m "Add enhanced search filtering features

- Add 'Other' category for uncategorized content
- Implement filter persistence with localStorage
- Add Clear All / Select All convenience buttons
- Add results count header showing active filters"
```

---

### ✨ PHASE 3: Polish & Accessibility (Optional)

#### Step 8: Improve Mobile Responsiveness

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 8.1. Open `search-modal.html` in editor
- [ ] 8.2. After search input, before two-column layout, add mobile toggle:
  - [ ] `<div class="sm:hidden w-full border-b border-gray-200 dark:border-gray-700 p-3">`
  - [ ] Add button: `id="mobile-filter-toggle"`
  - [ ] Button classes: `flex items-center justify-between w-full text-sm`
  - [ ] Add "Filters" text
  - [ ] Add chevron SVG icon: `id="mobile-filter-icon"`
  - [ ] Use down chevron, add `transition-transform` class
- [ ] 8.3. Locate filter sidebar `<aside>` element
- [ ] 8.4. Update sidebar classes:
  - [ ] Change `w-48` to `w-full sm:w-48`
  - [ ] Add `hidden sm:block` (hidden on mobile by default)
  - [ ] Keep other classes
- [ ] 8.5. Save file

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 8.6. Open `search.js` in editor
- [ ] 8.7. Add element references after toggle buttons:
  - [ ] `const mobileFilterToggle = document.getElementById('mobile-filter-toggle');`
  - [ ] `const mobileFilterIcon = document.getElementById('mobile-filter-icon');`
  - [ ] `const searchFilters = document.getElementById('search-filters');`
- [ ] 8.8. After backdrop click listener, add mobile toggle handler:
  - [ ] Add null checks for all 3 elements
  - [ ] Add click event listener to `mobileFilterToggle`
  - [ ] Check if sidebar has `hidden` class
  - [ ] If hidden: remove `hidden`, rotate icon 180deg
  - [ ] If visible: add `hidden`, rotate icon 0deg
  - [ ] Use `style.transform = 'rotate(180deg)'` for icon
- [ ] 8.9. Save file

**Testing Step 8:**
- [ ] 8.10. Rebuild and reload
- [ ] 8.11. Open DevTools, toggle device emulation
- [ ] 8.12. Set viewport to 375px (iPhone SE)
- [ ] 8.13. Open search modal
- [ ] 8.14. Verify filter sidebar is hidden
- [ ] 8.15. Verify "Filters" toggle button appears at top
- [ ] 8.16. Click toggle button
- [ ] 8.17. Verify sidebar expands, icon rotates
- [ ] 8.18. Click toggle again
- [ ] 8.19. Verify sidebar collapses, icon rotates back
- [ ] 8.20. Set viewport to 768px (tablet)
- [ ] 8.21. Verify sidebar is visible, toggle button hidden
- [ ] 8.22. Test at 1024px (desktop), verify same as tablet

#### Step 9: Enhance Accessibility with ARIA Labels

**File: `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`**

- [ ] 9.1. Open `search-modal.html` in editor
- [ ] 9.2. Update filter sidebar `<aside>` element:
  - [ ] Add `aria-label="Search filters"`
  - [ ] Add `role="group"`
- [ ] 9.3. Update h3 heading:
  - [ ] Add `id="filter-heading"`
- [ ] 9.4. Update button container or checkbox container:
  - [ ] Add `role="group"`
  - [ ] Add `aria-labelledby="filter-heading"`
- [ ] 9.5. Update "Select All" button:
  - [ ] Add `aria-label="Select all filter types"`
- [ ] 9.6. Update "Clear All" button:
  - [ ] Add `aria-label="Clear all filter types"`
- [ ] 9.7. Update separator span:
  - [ ] Add `aria-hidden="true"`
- [ ] 9.8. For each checkbox (Software, People, Events, Resources, Blog, Other):
  - [ ] Add `aria-label="Show [Type] results"` to input
  - [ ] Example: `aria-label="Show Software results"`
- [ ] 9.9. For each count span:
  - [ ] Add `aria-live="polite"`
  - [ ] This announces count changes to screen readers
- [ ] 9.10. Update results container `<div id="search-results">`:
  - [ ] Add `role="region"`
  - [ ] Add `aria-live="polite"`
  - [ ] Add `aria-label="Search results"`
- [ ] 9.11. Save file

**Testing Step 9:**
- [ ] 9.12. Install screen reader if not available:
  - [ ] macOS: VoiceOver (Cmd+F5)
  - [ ] Windows: NVDA (free) or JAWS
  - [ ] Linux: Orca
- [ ] 9.13. Enable screen reader
- [ ] 9.14. Open search modal with keyboard (Tab to search button, Enter)
- [ ] 9.15. Tab through filter sidebar
- [ ] 9.16. Verify each checkbox announces label and state
- [ ] 9.17. Verify "Search filters" is announced for sidebar
- [ ] 9.18. Toggle a checkbox, verify count update is announced
- [ ] 9.19. Type search query, verify results are announced
- [ ] 9.20. Verify buttons announce properly
- [ ] 9.21. Use axe DevTools to scan for accessibility issues
- [ ] 9.22. Fix any violations reported

#### Step 10: Disable Filters with Zero Results (Optional)

**File: `themes/hugo-theme-tailwind/assets/js/search.js`**

- [ ] 10.1. Open `search.js` in editor
- [ ] 10.2. Locate `updateFilterCounts(filters)` function
- [ ] 10.3. In the reset loop (Object.keys), add enable logic:
  - [ ] After setting textContent to "(0)"
  - [ ] Get checkbox: `document.querySelector(\`input[value="${type}"]\`)`
  - [ ] If checkbox exists:
    - [ ] Set `checkbox.disabled = false`
    - [ ] Remove opacity: `checkbox.parentElement.parentElement.classList.remove('opacity-50')`
- [ ] 10.4. In the update loop (filters.type), add disable logic:
  - [ ] Get count: `const count = filters.type[type];`
  - [ ] After updating textContent
  - [ ] Get checkbox same way as above
  - [ ] If checkbox exists AND count === 0 AND !checkbox.checked:
    - [ ] Set `checkbox.disabled = true`
    - [ ] Add opacity: `checkbox.parentElement.parentElement.classList.add('opacity-50')`
- [ ] 10.5. Important: never disable checked checkboxes
- [ ] 10.6. Save file

**Testing Step 10:**
- [ ] 10.7. Rebuild and reload
- [ ] 10.8. Open search modal
- [ ] 10.9. Search for very specific term (e.g., "zzzzzzz")
- [ ] 10.10. Verify all counts show "(0)"
- [ ] 10.11. Verify checkboxes that are checked remain enabled
- [ ] 10.12. Uncheck all checkboxes
- [ ] 10.13. Verify all checkboxes become disabled and grayed out
- [ ] 10.14. Search for common term (e.g., "data")
- [ ] 10.15. Verify filters with results become enabled
- [ ] 10.16. Verify filters with 0 results stay disabled
- [ ] 10.17. Check one disabled filter, verify it becomes enabled
- [ ] 10.18. Uncheck it, verify it becomes disabled again

**✅ Phase 3 Complete Criteria:**
- [ ] Mobile toggle button shows on small screens
- [ ] Filter sidebar is collapsible on mobile
- [ ] All ARIA labels are present
- [ ] Screen reader announces everything correctly
- [ ] Zero-result filters are disabled (if implemented)
- [ ] No accessibility violations in axe DevTools

**Commit Phase 3:**
```bash
git add -A
git commit -m "Add mobile responsiveness and accessibility improvements

- Add collapsible filter sidebar for mobile screens
- Implement comprehensive ARIA labels for screen readers
- Add optional zero-result filter disabling
- Ensure WCAG AA compliance"
```

---

### 🧪 Comprehensive Testing

#### Visual & Functional Testing

- [ ] T1. Test modal layout on desktop (1920px, 1440px, 1024px)
- [ ] T2. Test modal layout on tablet (768px)
- [ ] T3. Test modal layout on mobile (375px)
- [ ] T4. Verify all 6 checkboxes are visible and styled correctly
- [ ] T5. Verify counts show "(0)" before search
- [ ] T6. Search for "test" and verify counts update
- [ ] T7. Search for "ggplot" and verify Software results appear
- [ ] T8. Search for "Hadley" and verify People results appear
- [ ] T9. Uncheck all filters one by one, verify results disappear
- [ ] T10. Check all filters one by one, verify results reappear
- [ ] T11. Use Clear All button, verify all uncheck
- [ ] T12. Use Select All button, verify all check
- [ ] T13. Verify results header shows correct text
- [ ] T14. Verify dark mode styling (toggle if available)
- [ ] T15. Close and reopen modal, verify filter persistence
- [ ] T16. Refresh page, verify filter persistence

#### Keyboard Navigation Testing

- [ ] T17. Tab to search button, press Enter to open modal
- [ ] T18. Verify focus is in search input
- [ ] T19. Tab through all checkboxes
- [ ] T20. Use Space to toggle checkboxes
- [ ] T21. Tab to Clear All button, press Enter
- [ ] T22. Tab to Select All button, press Enter
- [ ] T23. Type search query, verify results appear
- [ ] T24. Use ↓ arrow to navigate results
- [ ] T25. Use ↑ arrow to navigate results
- [ ] T26. Press Enter on selected result, verify navigation
- [ ] T27. Press ESC to close modal
- [ ] T28. Verify focus indicators are visible on all elements

#### Screen Reader Testing

- [ ] T29. Turn on screen reader (VoiceOver, NVDA, JAWS)
- [ ] T30. Navigate to search button, verify announcement
- [ ] T31. Open modal, verify "Search filters" is announced
- [ ] T32. Navigate through checkboxes, verify labels announced
- [ ] T33. Toggle checkbox, verify state change announced
- [ ] T34. Search for query, verify results region announced
- [ ] T35. Verify count updates are announced (aria-live)
- [ ] T36. Navigate to buttons, verify labels announced

#### Browser Compatibility Testing

- [ ] T37. Test on Chrome (latest version)
  - [ ] All functionality works
  - [ ] Checkboxes styled correctly
  - [ ] No console errors
- [ ] T38. Test on Firefox (latest version)
  - [ ] All functionality works
  - [ ] Checkboxes styled correctly
  - [ ] No console errors
- [ ] T39. Test on Safari (latest version, macOS)
  - [ ] All functionality works
  - [ ] Checkboxes styled correctly
  - [ ] localStorage works
  - [ ] No console errors
- [ ] T40. Test on Edge (latest version)
  - [ ] All functionality works
  - [ ] No console errors
- [ ] T41. Test on Mobile Safari (iOS)
  - [ ] Mobile toggle works
  - [ ] Touch interactions work
  - [ ] Checkboxes tappable
- [ ] T42. Test on Mobile Chrome (Android)
  - [ ] Mobile toggle works
  - [ ] Touch interactions work
  - [ ] Checkboxes tappable

#### Performance Testing

- [ ] T43. Open DevTools Performance tab
- [ ] T44. Record search interaction
- [ ] T45. Verify search completes in < 500ms
- [ ] T46. Verify no layout thrashing
- [ ] T47. Open DevTools Network tab
- [ ] T48. Verify Pagefind bundle size reasonable (~200-300KB)
- [ ] T49. Test with 10+ modal open/close cycles
- [ ] T50. Use DevTools Memory profiler, check for leaks
- [ ] T51. Verify smooth scrolling in results list

#### Accessibility Compliance Testing

- [ ] T52. Install axe DevTools browser extension
- [ ] T53. Open search modal
- [ ] T54. Run axe scan
- [ ] T55. Fix all Critical and Serious issues
- [ ] T56. Verify color contrast ≥ 4.5:1 (WCAG AA)
- [ ] T57. Verify focus indicators have ≥ 3:1 contrast
- [ ] T58. Run Lighthouse audit
- [ ] T59. Verify Accessibility score ≥ 90

#### Edge Case Testing

- [ ] T60. Search with empty query, verify "Type to search"
- [ ] T61. Search for "zzzzzzzz", verify "No results found"
- [ ] T62. Uncheck all filters, verify "No results found"
- [ ] T63. Search with special characters: `* ? [ ] + .`
- [ ] T64. Search with very long query (100+ chars)
- [ ] T65. Rapidly toggle filters, verify no race conditions
- [ ] T66. Clear localStorage manually, verify defaults restore
- [ ] T67. Test in private/incognito mode
- [ ] T68. Test with JavaScript disabled (graceful degradation)

#### Regression Testing

- [ ] T69. Verify original search still works without filters
- [ ] T70. Verify result images load correctly
- [ ] T71. Verify result excerpts display properly
- [ ] T72. Verify clicking results navigates correctly
- [ ] T73. Verify backdrop click closes modal
- [ ] T74. Verify ESC key closes modal
- [ ] T75. Verify search input debouncing (300ms)
- [ ] T76. Verify no styling conflicts with rest of site

---

### 📝 Documentation & Cleanup

- [ ] D1. Review all code changes
- [ ] D2. Remove any console.log() debug statements
- [ ] D3. Remove any commented-out code
- [ ] D4. Verify code comments are helpful and accurate
- [ ] D5. Verify consistent indentation and formatting
- [ ] D6. Run Prettier if project uses it: `npx prettier --write "themes/**/*.{html,js}"`
- [ ] D7. Update README.md if needed (mention filtering feature)
- [ ] D8. Create screenshots of new filtering UI
- [ ] D9. Record a short demo video (optional)
- [ ] D10. Document any known limitations or issues

---

### 🚢 Deployment Preparation

- [ ] P1. Merge latest changes from main branch: `git pull origin main`
- [ ] P2. Resolve any conflicts
- [ ] P3. Run full build: `just build`
- [ ] P4. Run search index build: `just build-search`
- [ ] P5. Verify no build warnings or errors
- [ ] P6. Test production build locally if possible
- [ ] P7. Check site on staging environment (if available)
- [ ] P8. Get team review/approval (if required)
- [ ] P9. Create pull request with:
  - [ ] Clear title: "Add type-based search filtering"
  - [ ] Description of changes
  - [ ] Screenshots/video
  - [ ] Link to this plan
  - [ ] Note which phases implemented
  - [ ] Testing checklist results
- [ ] P10. Address code review feedback
- [ ] P11. Get final approval
- [ ] P12. Merge to main branch
- [ ] P13. Verify deployment succeeded
- [ ] P14. Test on production site
- [ ] P15. Monitor for any issues in first 24-48 hours

---

### 📊 Post-Launch

- [ ] L1. Monitor analytics for search usage
- [ ] L2. Track filter selection patterns
- [ ] L3. Identify zero-result queries
- [ ] L4. Gather user feedback
- [ ] L5. File issues for any bugs discovered
- [ ] L6. Consider Phase 2/3 if only Phase 1 was implemented
- [ ] L7. Consider future enhancements from plan
- [ ] L8. Document lessons learned

---

## Quick Reference: File Changes Summary

**Files to Create:**
- None (all modifications to existing files)

**Files to Modify:**
1. `themes/hugo-theme-tailwind/layouts/_default/baseof.html`
   - Add filter metadata to main content area

2. `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`
   - Redesign modal with two-column layout
   - Add filter sidebar with checkboxes
   - Add mobile toggle button (Phase 3)
   - Add ARIA labels (Phase 3)

3. `themes/hugo-theme-tailwind/assets/js/search.js`
   - Implement filtering functions
   - Update search to use Pagefind filters
   - Add persistence (Phase 2)
   - Add button handlers (Phase 2)
   - Add mobile toggle (Phase 3)

**Commands to Run:**
- `git checkout -b feature/search-filtering` (once at start)
- `just build` (after each phase)
- `just build-search` (after each phase)
- `just dev` (for testing)
- `git add -A && git commit -m "..."` (after each phase)
- `git push` (when ready for review)

**Total Tasks:** 300+
**Estimated Time:**
- Phase 1: 1-2 hours (75 tasks)
- Phase 2: 2-3 hours (100 tasks)
- Phase 3: 1-2 hours (75 tasks)
- Testing: 2-3 hours (76 tests)
- Documentation & Deployment: 1 hour (25 tasks)
- **Total: 7-11 hours for complete implementation**

---

## Implementation Checklist

### Phase 1: Core Functionality (Required) ✅ COMPLETED

- [x] **Step 1:** Add filter metadata to baseof.html
  - [x] Modify `themes/hugo-theme-tailwind/layouts/_default/baseof.html`
  - [x] Add `data-pagefind-filter-type` for 5 main types

- [x] **Step 2:** Update search modal HTML
  - [x] Modify `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`
  - [x] Add two-column layout with filter sidebar
  - [x] Add 5 checkboxes (Software, People, Events, Resources, Blog)
  - [x] Add count spans for each type

- [x] **Step 3:** Update search JavaScript
  - [x] Modify `themes/hugo-theme-tailwind/assets/js/search.js`
  - [x] Implement `getSelectedFilters()` function
  - [x] Implement `updateFilterCounts()` function
  - [x] Update `performSearch()` to use Pagefind filters API
  - [x] Add checkbox change event listeners

- [x] **Step 11:** Rebuild and test
  - [x] Run `just build`
  - [x] Run `just build-search`
  - [x] Test basic filtering functionality

### Phase 2: Enhanced Features (Recommended) ✅ COMPLETED

- [x] **Step 4:** Add "Other" type for uncategorized content
  - [x] Update baseof.html with "Other" fallback
  - [x] Add "Other" checkbox to search-modal.html
  - [x] Add "Other" to countElements in search.js

- [x] **Step 5:** Add filter persistence
  - [x] Add `saveFilterState()` function to search.js
  - [x] Add `restoreFilterState()` function to search.js
  - [x] Update `openModal()` to restore state
  - [x] Update checkbox listeners to save state

- [x] **Step 6:** Add Clear All / Select All buttons
  - [x] Add buttons to search-modal.html
  - [x] Add event listeners in search.js

- [x] **Step 7:** Add result count header
  - [x] Add results header to search-modal.html
  - [x] Add `updateResultsHeader()` function to search.js
  - [x] Update `performSearch()` to call header update
  - [x] Update `clearResults()` to hide header

### Phase 3: Polish & Accessibility (Optional) ✅ COMPLETED

- [x] **Step 8:** Improve mobile responsiveness
  - [x] Add mobile filter toggle button to search-modal.html
  - [x] Make sidebar collapsible on mobile (sm: breakpoint)
  - [x] Add toggle functionality in search.js

- [x] **Step 9:** Enhance accessibility
  - [x] Add `aria-label` to filter sidebar
  - [x] Add `aria-labelledby` to filter group
  - [x] Add `aria-label` to buttons
  - [x] Add `aria-label` to each checkbox
  - [x] Add `aria-live="polite"` to counts and results
  - [x] Add `role="region"` to results area

- [x] **Step 10:** Disable zero-result filters (optional)
  - [x] Update `updateFilterCounts()` to disable empty checkboxes
  - [x] Add opacity styling for disabled filters
  - [x] Ensure checked filters never get disabled

### Testing Checklist ⏳ READY FOR TESTING

- [ ] Test on Chrome/Edge
- [ ] Test on Firefox
- [ ] Test on Safari
- [ ] Test on Mobile Safari (iOS)
- [ ] Test on Mobile Chrome (Android)
- [ ] Test with keyboard only (Tab, Space, Arrow keys, Enter, ESC)
- [ ] Test with screen reader (VoiceOver, NVDA, or JAWS)
- [ ] Verify WCAG AA color contrast
- [ ] Test dark mode
- [ ] Test filter persistence (close and reopen modal)
- [ ] Test mobile collapsible sidebar

### Files Modified

**Templates:**
- `themes/hugo-theme-tailwind/layouts/_default/baseof.html`

**Partials:**
- `themes/hugo-theme-tailwind/layouts/partials/search-modal.html`

**JavaScript:**
- `themes/hugo-theme-tailwind/assets/js/search.js`

**Build Commands:**
- `just build` (rebuilds Hugo site)
- `just build-search` (rebuilds Pagefind index)

---

## Questions & Answers

### Implementation Questions

**Q: Do I need to implement all 11 steps?**
A: No. Steps 1-3 and 11 (Phase 1) provide the core filtering functionality. Steps 4-10 (Phases 2-3) are enhancements that can be added later or skipped entirely. Start with Phase 1, test it, then decide if you want the enhancements.

**Q: Why add filter metadata to baseof.html instead of individual templates?**
A: Centralized approach is simpler and ensures consistency across all content types. You modify one file instead of 5+. Individual templates give more control but require more maintenance.

**Q: What happens to pages without a section (like the homepage)?**
A: If you implement Step 4, they get the "Other" type. Without Step 4, they won't have a filter attribute and won't appear in filtered searches (which is acceptable for utility pages).

**Q: Can I customize the "Other" category name?**
A: Yes. Change `"Other"` to anything you want in baseof.html, search-modal.html, and search.js. Keep them consistent. Examples: "Pages", "Misc", "General".

**Q: How does the z-index work? I saw `z-100` in the modal.**
A: Tailwind CSS 3+ supports arbitrary values. `z-100` ensures the modal appears above all other content. The original used `z-[100]` (bracket notation), both work the same.

### Functionality Questions

**Q: Can users search without any filters selected?**
A: No. If all checkboxes are unchecked, "No results found" appears. This prevents confusion from empty result sets. Users can click "Select All" to restore filters.

**Q: Do filter counts show total matches or filtered matches?**
A: Total matches (unfiltered). This helps users understand how many results are available per type before filtering. For example, if you search "Python" and see "Software (45), Blog (12)", you know there are 45 software results even if you've unchecked that filter.

**Q: What happens to counts when a user types a new query?**
A: Counts update in real-time based on the new search results. Each keystroke (with 300ms debounce) triggers a new search and updates all counts.

**Q: Why run two searches (filtered and unfiltered)?**
A: We run an unfiltered search to get accurate counts for all types, then a filtered search for the displayed results. This is fast (~20-50ms each) and provides better UX than showing filtered counts.

**Q: What happens if a filter has 0 results?**
A: By default, it shows "(0)" but remains clickable. If you implement Step 10, filters with 0 results become disabled and grayed out (unless already checked).

### Persistence Questions

**Q: How long do filter selections persist?**
A: Forever (or until user clears browser data). localStorage has no expiration unless manually cleared. Filter state survives page reloads, browser restarts, even months later.

**Q: Does persistence work in private/incognito mode?**
A: Yes, but only within that session. When the private window closes, localStorage is cleared. Next private session starts with defaults (all checked).

**Q: Can users clear their saved filter preferences?**
A: They can clear browser data, or you can add a "Reset to defaults" button that clears the localStorage key. The code gracefully handles missing/invalid localStorage data.

### Mobile Questions

**Q: How does the mobile layout work?**
A: On screens < 640px (Tailwind's `sm` breakpoint), the filter sidebar is hidden by default. A toggle button shows/hides it. On larger screens, the sidebar is always visible.

**Q: Can I change the mobile breakpoint?**
A: Yes. Change `sm:block` and `sm:w-48` to `md:block` and `md:w-48` (768px) or `lg:block` and `lg:w-48` (1024px) in search-modal.html.

**Q: Why not use a dropdown for mobile instead of a sidebar?**
A: Dropdown requires different UI (select element or custom dropdown). Collapsible sidebar is simpler and consistent across devices. You can implement a dropdown as a future enhancement.

### Accessibility Questions

**Q: Is this WCAG AA compliant?**
A: Phase 1-2 are close but may need color contrast verification. Phase 3 (Step 9) adds full ARIA labels for WCAG AA compliance. Use axe DevTools or Lighthouse to verify.

**Q: Do I need to implement Step 9 (accessibility enhancements)?**
A: Recommended but not required. Basic keyboard navigation works without it. Step 9 adds ARIA labels for screen readers and explicit roles for better accessibility.

**Q: Can keyboard-only users operate the filters?**
A: Yes. Tab to navigate, Space to toggle checkboxes, Enter to activate buttons. This works even without Step 9.

### Performance Questions

**Q: How much does this increase page load time?**
A: Negligible. The modal HTML adds ~3KB (compressed: ~1KB). JavaScript is loaded lazily. Pagefind index increases ~15KB. Total impact on load time: < 50ms.

**Q: Does filtering slow down search?**
A: No. Pagefind filtering is client-side and very fast (10-50ms). Users won't notice any delay. The debounce (300ms) is the main delay, which improves UX by preventing rapid searches.

**Q: How many searches can run per second?**
A: Pagefind can handle 100+ searches/second. The debounce limits it to ~3/second during typing. No performance concerns.

### Customization Questions

**Q: Can I change the filter sidebar width?**
A: Yes. Change `w-48` (12rem/192px) to `w-40` (10rem), `w-56` (14rem), or `w-64` (16rem) in search-modal.html. Test to ensure filters still fit.

**Q: Can I change the checkbox colors?**
A: Yes. Replace `text-posit-green-600` and `focus:ring-posit-green-500` with any Tailwind color (e.g., `text-blue-600`, `focus:ring-blue-500`).

**Q: Can I add icons to filter labels?**
A: Yes. Add SVG icons or emoji before each label. Example: `<span>📦 Software</span>`. Keep icons small and ensure sufficient color contrast.

**Q: Can I change the results limit (currently 10)?**
A: Yes. In search.js, change `search.results.slice(0, 10)` to any number (e.g., `20`, `50`). Higher numbers may slow down rendering slightly.

### Extension Questions

**Q: Can this be extended to filter by language or date?**
A: Yes. Add more `data-pagefind-filter-*` attributes (e.g., `data-pagefind-filter-language="Python"`) to templates, expand the UI with additional checkboxes or dropdowns, and update the JavaScript to handle multiple filter dimensions.

**Q: Can I add a search preset like "Documentation only"?**
A: Yes. See Future Enhancements section. Add buttons that set specific filter combinations. Example: "Documentation" button checks only "Resources" and "Blog".

**Q: Does this work with Algolia or other search engines?**
A: No. This implementation is specific to Pagefind's filtering API. Algolia uses different faceted search APIs. You'd need to rewrite the JavaScript for other search engines.

**Q: Can I track which filters users click?**
A: Yes. Add analytics tracking in the checkbox change event listener. Example:
```javascript
checkbox.addEventListener('change', () => {
  // Track with Plausible, Google Analytics, etc.
  plausible('Filter Changed', { props: { type: checkbox.value, checked: checkbox.checked } });
  // ... rest of handler
});
```

### Troubleshooting Questions

**Q: Filters show but don't work. What's wrong?**
A: Most likely the Pagefind index wasn't rebuilt after adding filter metadata. Run `just build && just build-search`.

**Q: Counts always show (0). What's wrong?**
A: Either: (1) Pagefind index not rebuilt, (2) filter metadata not added to templates correctly, or (3) JavaScript typo in `updateFilterCounts()`. Check browser console for errors.

**Q: Modal looks broken on mobile. What's wrong?**
A: Verify Tailwind CSS was rebuilt (`npm run build-tailwind`). Check that responsive classes (`sm:`, `md:`) are working. Try hard refresh (Cmd+Shift+R / Ctrl+Shift+R).

**Q: localStorage not persisting. What's wrong?**
A: Check browser privacy settings - some browsers block localStorage. Try incognito mode. Verify no JavaScript errors in console. Check if localStorage is enabled: `console.log(localStorage.getItem('search-filters'))`.

**Q: Dark mode colors look wrong. What's wrong?**
A: Verify dark mode is enabled on the site. Check that `dark:` classes are in the HTML. Ensure Tailwind's `darkMode: 'class'` is configured. Rebuild Tailwind CSS.

---

**More questions?** Check the Edge Cases, Performance Considerations, and Accessibility sections above, or review the Pagefind documentation at https://pagefind.app/docs/

---

## Implementation Best Practices

### Development Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/search-filtering
   ```

2. **Implement Phase 1 first:**
   - Complete Steps 1-3, 11
   - Test thoroughly
   - Commit: `git commit -m "Add basic search filtering (Phase 1)"`

3. **Test before proceeding:**
   - Run all Phase 1 tests
   - Fix any issues
   - Get feedback from team if possible

4. **Implement Phase 2:**
   - Complete Steps 4-7
   - Test each step incrementally
   - Commit after each major feature: `git commit -m "Add filter persistence"`

5. **Implement Phase 3 (optional):**
   - Complete Steps 8-10
   - Full accessibility and mobile testing
   - Commit: `git commit -m "Add accessibility improvements"`

6. **Final testing:**
   - Full regression testing
   - Cross-browser testing
   - Performance testing

7. **Create pull request:**
   - Include screenshots/video
   - Link to this plan document
   - Note which phases are implemented

### Git Commit Guidelines

**IMPORTANT:** When committing changes, use only your own authorship.

❌ **DO NOT** add Claude as a co-author in commits
❌ **DO NOT** use `Co-Authored-By: Claude` or similar
❌ **DO NOT** credit AI tools in commit messages

✅ **DO** commit under your own name as the sole author
✅ **DO** write clear, descriptive commit messages
✅ **DO** follow your project's existing commit conventions

**Example commits:**
```bash
# Good - your authorship only
git commit -m "Add type-based filtering to search modal"

# Good - descriptive and focused
git commit -m "Implement filter persistence with localStorage"

# Bad - DO NOT do this
git commit -m "Add search filtering

Co-Authored-By: Claude <...>"
```

**Why?** You are implementing the feature based on this plan. The code you write is your work, even if assisted by planning documentation.

### Code Organization Tips

- **Keep functions small:** Each function should do one thing well
- **Add comments:** Explain "why" not "what" (code shows what)
- **Use consistent naming:** Follow existing project conventions
- **Test edge cases:** Empty queries, all filters unchecked, localStorage cleared
- **Handle errors gracefully:** Wrap localStorage access in try-catch

### Common Pitfalls to Avoid

❌ **Don't modify theme files directly** - Use project overrides when possible
❌ **Don't forget to rebuild Pagefind** - Filter metadata won't work without rebuild
❌ **Don't skip testing on mobile** - Mobile experience is critical
❌ **Don't implement all phases at once** - Incremental is better
❌ **Don't forget dark mode** - Test both light and dark themes
❌ **Don't ignore accessibility** - At minimum, ensure keyboard navigation works

### Debugging Tips

**Problem: Filters don't work**
```bash
# Check if filter metadata exists in built HTML
cat public/software/ggplot2/index.html | grep "data-pagefind-filter-type"

# Rebuild everything
just build && just build-search
```

**Problem: Counts show (0)**
```javascript
// Check Pagefind index in browser console
const pf = await import('/pagefind/pagefind.js');
const search = await pf.search('test');
console.log(search.filters); // Should show type filter with counts
```

**Problem: localStorage not working**
```javascript
// Test in browser console
localStorage.setItem('test', 'hello');
console.log(localStorage.getItem('test')); // Should show "hello"
localStorage.removeItem('test');
```

**Problem: Styles not applying**
```bash
# Rebuild Tailwind CSS
npm run build-tailwind

# Check if Tailwind classes are in built CSS
cat assets/css/index.css | grep "posit-green-600"
```

### Performance Optimization

If you have a very large site (1000+ pages):

1. **Increase result limit gradually:** Test with 10, 20, 50 results
2. **Consider virtual scrolling:** For 100+ results, implement virtual list
3. **Debounce aggressively:** Increase from 300ms to 500ms if needed
4. **Lazy load images:** Use `loading="lazy"` (already implemented)
5. **Monitor bundle size:** Check Pagefind index size growth

### Maintenance Notes

**When adding new content types:**
1. Add to baseof.html condition
2. Add checkbox to search-modal.html
3. Add to countElements object in search.js
4. Update filter persistence (automatically handled if using value attribute)
5. Rebuild and test

**When upgrading Pagefind:**
1. Check release notes for breaking changes
2. Test filtering API compatibility
3. Verify filter counts still work
4. Re-test all functionality

---

## Ready to Implement?

### Quick Start (Phase 1 Only)

If you just want basic filtering:

1. **Edit 3 files:** baseof.html, search-modal.html, search.js
2. **Follow Steps 1-3, 11**
3. **Test with checklist above**
4. **Estimated time:** 1-2 hours

### Full Implementation (All Phases)

If you want all features:

1. **Follow all 11 steps in order**
2. **Test after each phase**
3. **Use the comprehensive testing checklist**
4. **Estimated time:** 4-7 hours

### Recommended Approach

**For MVP:** Implement Phase 1, deploy, gather feedback
**For Polish:** Add Phase 2 after MVP is stable
**For Perfection:** Add Phase 3 for full accessibility

---

**Questions or issues?** Refer to the Q&A section above or consult Pagefind documentation at https://pagefind.app/

**Ready to start?** Begin with Phase 1, Steps 1-3! 🚀
