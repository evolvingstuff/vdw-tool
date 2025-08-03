# Build Pipeline Porting Plan

## Overview
Port the build pipeline components from the vitD project into vdw-tool to create a clean separation between conversion (vitD) and build (vdw-tool) processes.

## Deployment Architecture Change
**Previous**: Generated site in separate directory for GitHub/Amplify integration with git hooks
**New**: Generate site for direct CloudFront hosting (more reliable, less fragile than Amplify git hooks)

## Current State Analysis

### What vitD Currently Does (Build-Related)
From analyzing `hugo.py` and related files:

1. **Hugo Site Generation** 
   - Creates fresh Hugo site structure
   - Copies custom layouts and themes
   - Manages configuration files

2. **Content Processing**
   - Tag expansion using ontology engine
   - Cooccurrence analysis for tag relationships
   - Search data generation

3. **Static Site Optimization**
   - Pagefind indexing for full-text search
   - Static file copying (CSS, JS, attachments)
   - Asset optimization

4. **Advanced Features**
   - Context group processing
   - Text-to-tag mapping
   - Negation handling for queries

## Architecture Design

### New Actions Structure
```
_src/actions/
├── build_hugo.py              # ✅ ENHANCED - Custom layouts, static files, FAIL FAST, search integration
├── serve_hugo.py              # ✅ Enhanced with port conflict resolution  
├── sync_posts_from_s3.py      # ✅ Enhanced with tqdm progress, pagination
├── convert_tiki_data.py        # 🆕 TikiWiki JSON to Markdown conversion
└── deploy_to_cloudfront.py    # 🆕 Direct CloudFront deployment

_src/utils/
├── build_search_index.py      # ✅ DONE - Pagefind integration
├── generate_search_data.py    # ✅ DONE - Search suggestions & metadata
├── ontology_engine.py         # ✅ DONE - Core ontology processing
├── ontology_utils.py          # ✅ DONE - Ontology parsing utilities
├── tag_processor.py           # ✅ DONE - Tag expansion logic
├── conversion_utils.py        # 🆕 Data conversion utilities
├── content_cleaner.py         # 🆕 Content cleaning and conversion
├── attachment_handler.py      # 🆕 File and attachment management
└── build_utils.py             # 🆕 Build helper functions
```

### Infrastructure Enhancements ✅ COMPLETED
- ✅ **Docker auto-start** - Automatically detects and starts Docker Desktop
- ✅ **Port conflict resolution** - Kills processes using port 1313 safely
- ✅ **FAIL FAST philosophy** - No silent failures, immediate clear error messages
- ✅ **Enhanced user experience** - Works seamlessly for non-technical users

## Components to Port

### Phase 1: Core Build Enhancement (Priority: High)

#### 1.1 Enhanced Hugo Build (`build_hugo.py`)
**Source**: `hugo.py:391-537`
- **Current**: Basic Hugo site generation
- **Enhancement**: Add custom layout copying, config management
- **Key Features**:
  - Custom layout copying from `hugo_stuff/`
  - Static file optimization
  - Build error handling and recovery
  - Directory cleaning with hidden file preservation

#### 1.2 Static File Management (`optimize_static_files.py`)
**Source**: `hugo.py:186-193`, `hugo.py:431-442`
- **Purpose**: Copy and optimize CSS, JS, images
- **Key Features**:
  - Asset copying with directory structure preservation
  - File compression and optimization
  - Cache busting for updated assets

### Phase 2: Search & Indexing (Priority: High)

#### 2.1 Pagefind Integration (`build_search_index.py`)
**Source**: `hugo.py:507-531`
- **Purpose**: Full-text search indexing (LOCAL FIRST)
- **Key Features**:
  - Pagefind CLI integration with local Hugo output
  - Custom indexing configuration for `hugo_output/`
  - Selective content indexing (posts/**/*.html)
  - Test search functionality with local Python server
  - Verify search UI integration works at localhost:1313

#### 2.2 Search Data Generation (`generate_search_data.py`)
**Source**: Referenced in vitD static files, `hugo_stuff/static/js/`
- **Purpose**: Generate search suggestions and metadata (LOCAL FIRST)
- **Key Features**:
  - Text suggestions JSON generation for auto-complete
  - Page metadata extraction for search results
  - JavaScript integration files (search.js, search-suggestions.js)
  - Local testing of search functionality
  - Auto-complete data structures working in browser

### Phase 3: Content Intelligence (Priority: Medium)

#### 3.1 Ontology Processing (`process_ontology.py`)
**Source**: `ontology_parse.py`, `hugo.py:458-480`
- **Purpose**: Tag expansion and relationship processing
- **Key Features**:
  - Load and parse ontology rules from `ontology.txt`
  - Tag implication processing (A => B)
  - Tag associations (A ~ B)  
  - Tag equality (A = B)
  - Context group processing ((A + B) => C)
  - Text-to-tag mapping

#### 3.2 Tag Processing (`tag_processor.py`)
**Source**: `hugo.py:258-388`, `ontology_parse.py:683-733`
- **Purpose**: Core tag expansion logic
- **Key Features**:
  - Process markdown frontmatter
  - Expand tags using ontology rules
  - Generate tag slugs
  - Handle tag inheritance and transitivity

#### 3.3 Content Analysis (`analyze_content.py`)
**Source**: `utils/cooccurrence_tracker.py`
- **Purpose**: Analyze content relationships
- **Key Features**:
  - Tag cooccurrence tracking
  - Content similarity analysis
  - Related content suggestions
  - Analytics data generation

### Phase 4: Advanced Features (Priority: Low) 

#### 4.1 CloudFront Deployment (`deploy_to_cloudfront.py`)
**Source**: New functionality (replacing Amplify git hooks)
- **Purpose**: Direct CloudFront deployment
- **Key Features**:
  - S3 bucket sync for static assets
  - CloudFront cache invalidation
  - Build artifact management
  - Deployment verification

#### 4.2 Performance Optimization
- **Incremental builds**: Only rebuild changed content
- **Caching**: Cache ontology processing results
- **Parallel processing**: Multi-threaded build pipeline

#### 4.3 Build Analytics
- **Build performance metrics**
- **Content statistics** 
- **Tag usage analytics**
- **Build failure reporting**

## Dependencies to Add

### Python Packages
```
# Add to requirements.txt
nltk>=3.8.1                   # For stopwords and text processing
frontmatter>=3.0.8            # For markdown frontmatter parsing
boto3>=1.34.144               # For S3/CloudFront deployment (already exists)
```

### System Dependencies  
```
# Add to Dockerfile
pagefind                      # Search indexing tool
```

## Configuration Changes

### Hugo Configuration Enhancements
- Enhanced `hugo_stuff/hugo.toml` with:
  - Search configuration
  - Tag taxonomy settings
  - Custom URL structures
  - Performance optimizations

### New Configuration Files
- `ontology.txt`: Tag relationship definitions
- `build_config.json`: Build pipeline settings
- `search_config.json`: Search behavior configuration

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETED
1. ✅ **DONE** - Enhanced `build_hugo.py` with custom layouts, config management
2. ✅ **DONE** - Static file optimization (complete directory copying)
3. ✅ **DONE** - Build error handling (FAIL FAST AND LOUD philosophy)
4. ✅ **DONE** - Updated requirements.txt (nltk, frontmatter) and Dockerfile (Pagefind)
5. ✅ **DONE** - Renamed master_script.py to app.py with menu improvements
6. ✅ **DONE** - Directory cleaning with hidden file preservation

### Phase 2: Search Integration ✅ COMPLETED - LOCAL FIRST
1. ✅ **DONE** - Pagefind integration and indexing (creates pagefind/ directory)
2. ✅ **DONE** - Search data generation (cooccurrences.json, text_suggestions.json)
3. ✅ **DONE** - JavaScript search functionality integration (existing search.js works)
4. ✅ **DONE** - Search UI components working locally at localhost:1313
5. ✅ **DONE** - Enhanced search suggestions from real tag relationships
6. ✅ **DONE** - FAIL FAST error handling throughout search pipeline
7. ✅ **DONE** - Automatic search integration in Hugo build workflow

### Phase 3: Content Intelligence ✅ COMPLETED
1. ✅ **DONE** - Port ontology engine (OntologyEngine class from ontology_parse.py)
2. ✅ **DONE** - Create ontology parsing utilities (parse ontology rules: A => B, A ~ B, A = B)
3. ✅ **DONE** - Implement tag expansion logic (process markdown frontmatter, expand tags)
4. ✅ **DONE** - Create content analysis tools (cooccurrence tracking, tag relationships)
5. ✅ **DONE** - Integrate ontology processing into Hugo build workflow
6. ✅ **DONE** - Add ontology.txt configuration support
7. ✅ **DONE** - Test tag expansion with real vitamin D content
8. ✅ **DONE** - Fix critical frontmatter format preservation bug (JSON vs YAML)

### Phase 4: Data Conversion Integration (Week 4) - CURRENT PHASE
**Overview**: Port TikiWiki to Markdown conversion from vitD for complete end-to-end pipeline

**Data Flow**:
```
data/ (gitignored, copied from vitD)
  ├── tiki_pages_*.json          # Page content with TikiWiki markup
  ├── tiki_categories_*.json     # Category definitions
  ├── tiki_wiki_attachments_*.json # File attachments (skip for now)
  ├── catId-to-catName.csv       # Category ID to name mapping
  ├── pageId-to-catId.csv        # Page to category relationships
  └── rosetta.csv                # Category name remapping
    ↓ CONVERSION PROCESS
posts/ 
  └── *.md                       # Markdown files with JSON frontmatter
    ↓ EXISTING HUGO BUILD PIPELINE
Hugo Site (with ontology tag expansion + search)
```

**Tasks**:
1. 🆕 Port core conversion logic from vitD main.py and utils/utils.py
2. 🆕 Create `convert_tiki_data.py` action (replace Hello World action)
3. 🆕 Port TikiWiki markup parser (parsing/parser.py) for content conversion
4. 🆕 Port data models (Page, Category, Attachment) and JSON loading functions
5. 🆕 Port slug generation utilities for post filenames and URLs
6. 🆕 Generate JSON frontmatter (title, slug, aliases, categories, date, tiki_page_id)
7. 🆕 Integrate conversion action into main app.py menu
8. 🆕 Test complete pipeline: data/ → posts/ → Hugo Build

**Scope Limitations**:
- ❌ **Skip attachment handling** for initial implementation  
- ✅ **Focus on core content conversion** (TikiWiki markup → Markdown)
- ✅ **Maintain existing Hugo build pipeline** compatibility

### Phase 5: Deployment & Optimization (Week 5)
1. 🆕 CloudFront deployment integration
2. 🆕 Performance optimization  
3. 🆕 Build analytics
4. 🆕 Documentation
5. 🆕 Complete testing suite

## Success Criteria

### Functional Requirements (Local Development Priority)
- [ ] Build pipeline processes markdown files with tag expansion
- [ ] **Pagefind search works with full-text indexing at localhost:1313**
- [ ] **JavaScript search suggestions working in browser**
- [ ] **Search UI integrated and functional locally**
- [ ] Tag relationships are properly expanded and displayed
- [ ] Static site builds are faster than vitD hugo.py
- [ ] All existing hugo_stuff configuration is preserved

### Performance Requirements  
- [ ] Build time < 2 minutes for 1000+ posts
- [ ] Tag expansion < 5 seconds for typical content
- [ ] Search indexing < 30 seconds for full site
- [ ] Memory usage < 1GB during build

### Quality Requirements
- [ ] Modular, testable code architecture  
- [ ] Comprehensive error handling
- [ ] Progress indicators for long operations
- [ ] Detailed build logging and diagnostics

## Risks & Mitigation

### Technical Risks
1. **Ontology complexity**: Start with simple tag expansion, add complexity gradually
2. **Performance issues**: Profile and optimize critical paths  
3. **Hugo compatibility**: Test with multiple Hugo versions
4. **Search integration**: Have fallback search options

### Process Risks  
1. **Scope creep**: Stick to essential features first
2. **Compatibility**: Maintain backward compatibility with existing content
3. **Testing**: Build comprehensive test suite as we go

## Files to Reference from vitD

### Core Files
- `hugo.py`: Main build logic and Hugo integration
- `ontology_parse.py`: Complete ontology engine implementation  
- `config.py`: Configuration patterns and options
- `models.py`: Data structures for pages, categories, attachments

### Utility Files
- `utils/ontology_utils.py`: Ontology parsing utilities
- `utils/cooccurrence_tracker.py`: Content relationship analysis
- `utils/slugs.py`: URL slug generation logic
- `utils/titles.py`: Title processing utilities

### Configuration Files
- `docs_hugo/`: Hugo theme and layout files
- `ontology.txt`: Tag relationship definitions
- `pagefind.yml`: Search configuration

This plan provides a roadmap for systematically porting the build functionality while maintaining clean architecture and avoiding the complexity of the conversion logic.