# VDW Tool - Project Plan

## Overview
A Dockerized administration tool for managing dad's website. The tool centralizes all development within the `src/` directory and uses Docker to eliminate the need for local installation of Python, npm, and other dependencies.

## Project Structure
```
vdw-tool/
├── src/                    # All development code
│   └── master_script.py    # Main Python script with multiple options
├── docs/                   # Documentation
├── Dockerfile              # Container definition
├── docker-compose.yml      # Service orchestration
└── README.md              # User instructions
```

## Phase 1: Dockerization Setup

### Goals
- [x] Basic project structure with src/ organization
- [x] Create Dockerfile for Python environment
- [ ] Set up docker-compose.yml for easy execution
- [x] Test containerized execution of master_script.py
- [ ] Create simple README for dad's usage

### Docker Implementation Plan
1. **Base Container**: Python slim image with necessary dependencies
2. **Volume Mounting**: Map src/ directory for development
3. **Entry Point**: master_script.py as the main execution point
4. **Port Exposure**: If web interface is added later

### Future Phases
- **Phase 2**: Add web interface options to master_script.py
- **Phase 3**: Website management features
- **Phase 4**: Additional administration tools

## Docker Distribution & Usage

**Approach**: Simple build scripts for both platforms
- **Dad (Windows)**: `build.bat` - Double-click to build and run
- **You (Mac)**: `build.sh` - Execute to build and run for testing

**Files Created:**
- `src/Dockerfile` - Container definition with Python environment
- `build_docker.bat` - Windows script with error handling and pause
- `build_docker.sh` - Mac/Linux script for testing

**Usage:**
- Dad just needs to double-click `build_docker.bat`
- You can run `./build_docker.sh` for testing
- Both scripts build the container and run it interactively

## Development Notes
- Keep main directory clean - all code in src/
- Use Docker for all dependencies
- Master script will expand with multiple administration options
- Focus on ease of use for non-technical user