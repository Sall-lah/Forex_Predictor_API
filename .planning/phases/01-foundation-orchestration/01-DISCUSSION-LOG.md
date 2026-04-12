# Phase 1 Discussion Log

## Topic: Project Structure

**Question 1: Root Dependency Management**
*How should we manage the root-level scripts that boot both the Python API and the Web frontend?*
**User Selected:** Task Runner Root (A lightweight package.json at the root purely for running 'concurrently' to boot both apps, with all Node dependencies living inside 'web/package.json')

**Question 2: Web Directory Structure**
*Inside the new 'web/' directory, how do you want to structure the Express Backend-For-Frontend and the React application?*
**User Selected:** Integrated Web App (A single package.json in 'web/'. Express acts as the development API proxy and serves the built React static files in production.)

---
**Status:** Discussion for Phase 1 concluded. Ready for planning phase.