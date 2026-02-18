# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains OpenSCAD designs for tooling/fixtures used with nixie tubes (specifically IN-18 tubes).

## Build Commands

Render SCAD to STL:
```bash
openscad -o IN-18_Lead_Forming_Tool.stl IN-18_Lead_Forming_Tool.scad
```

Preview in OpenSCAD GUI:
```bash
openscad IN-18_Lead_Forming_Tool.scad
```

## OpenSCAD Conventions

- Use `$fn = 120` (or similar high value) for smooth curves in final renders
- Center parts with `center = true` for easier positioning
- Use `difference()` to cut features from solid bodies
- Parametric variables at top of file for easy adjustment

## 3D Printing

- Parts will be printed on a Prusa Mk3S+ in PETG
- If dimensions are adjusted for printability (tolerances, clearances, wall thickness, etc.), add a comment explaining the change

## Git

- Do not add Claude attribution to commit messages
