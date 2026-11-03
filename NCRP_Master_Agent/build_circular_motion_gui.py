# -*- coding: utf-8 -*-
"""
Build and deploy the Circular Orbital Motion Visualizer for FIR 281/2026 (ACK: 30809260089905)
Features:
- Dual Layout Engine: ⭕ Circular Orbit View (Default) + 📐 3D Columns View
- Concentric Orbital Rings (Layer 1 Mule Orbit, Layer 2 Routing Orbit, Terminal ATM/Lien Orbit)
- High-tech Rotating Radar Sweep Scanner with Conical Glow
- 60 FPS Real-time Moving Money Packets (₹99,000, ₹95,000, ₹4,000, ₹76,582.90, ₹21,917.10, etc.)
- Comet particle trails, impact shockwaves, and circular orbital circulation
- Interactive Stepper (Step 1-5), Narrative in English & Hindi, 3D Camera Controls, Search & Entity Dossier
"""

import os
import shutil

OUTPUT_PATHS = [
    r"D:\agent\NCRP Compalint Againt\NCRP_Master_Agent\output\FIR_281_2026\money_trail_3d_visualizer_30809260089905.html",
    r"D:\agent\NCRP Compalint Againt\NCRP_Master_Agent\templates\money_trail_3d_template.html",
    r"C:\Users\Hackthebox\.gemini\antigravity\brain\0a03e3cc-6ebc-4335-a186-beeec69269f8\money_trail_3d_gui.html"
]

HTML_CONTENT = r'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CIRCULAR ORBITAL MONEY TRAIL 3D | LIVE FRAUD FLOW | FIR 281/2026</title>
    <style>
        :root {
            --bg-base: #030712;
            --bg-surface: #080e1e;
            --bg-elevated: #0f172a;
            --bg-card: rgba(11, 18, 34, 0.92);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(0, 240, 255, 0.5);
            --text-main: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --col-victim: #ef4444;
            --col-l1: #f59e0b;
            --col-l2: #06b6d4;
            --col-l3: #a855f7;
            --col-hold: #10b981;
            --col-atm: #f97316;
            --col-cyan: #00f0ff;
            --col-gold: #fbbf24;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", "Helvetica Neue", Arial, sans-serif;
            user-select: none;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            overflow: hidden;
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Top Institutional Header */
        header {
            background: linear-gradient(180deg, #0c1527 0%, #040814 100%);
            border-bottom: 1px solid rgba(0, 240, 255, 0.25);
            padding: 10px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
            box-shadow: 0 4px 25px rgba(0, 0, 0, 0.75);
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .crest-wrapper {
            position: relative;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle, #1e293b 0%, #0f172a 100%);
            border: 2px solid var(--col-gold);
            border-radius: 50%;
            box-shadow: 0 0 16px rgba(251, 191, 36, 0.45);
        }

        .crest-wrapper svg {
            width: 24px;
            height: 24px;
            fill: var(--col-gold);
        }

        .brand-meta h1 {
            font-size: 15px;
            font-weight: 800;
            letter-spacing: 0.6px;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .live-tag {
            font-size: 10px;
            font-weight: 800;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(239, 68, 68, 0.18);
            color: var(--col-victim);
            border: 1px solid rgba(239, 68, 68, 0.45);
            display: inline-flex;
            align-items: center;
            gap: 5px;
            text-transform: uppercase;
        }

        .pulse-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--col-victim);
            box-shadow: 0 0 10px var(--col-victim);
            animation: blink 1.1s infinite alternate;
        }
        @keyframes blink { 0% { opacity: 0.25; } 100% { opacity: 1; } }

        .brand-meta p {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .meta-chip {
            color: var(--col-cyan);
            background: rgba(0, 240, 255, 0.1);
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid rgba(0, 240, 255, 0.25);
            font-family: monospace;
            font-size: 11px;
        }

        /* Layout Switcher Pill in Center Header */
        .layout-switcher {
            display: flex;
            align-items: center;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 30px;
            padding: 3px 4px;
            gap: 4px;
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.15);
        }

        .btn-layout {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.25s ease;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        .btn-layout.active {
            background: linear-gradient(135deg, #0284c7 0%, #00f0ff 100%);
            color: #030712;
            box-shadow: 0 0 16px rgba(0, 240, 255, 0.6);
            font-weight: 900;
        }

        .btn-layout:hover:not(.active) {
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }

        /* Action Toolbar in Header */
        .header-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-act {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }

        .btn-act:hover {
            border-color: var(--col-cyan);
            color: #fff;
            background: rgba(0, 240, 255, 0.12);
        }

        .btn-act.active-glow {
            background: rgba(0, 240, 255, 0.18);
            border-color: var(--col-cyan);
            color: var(--col-cyan);
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.35);
        }

        .btn-act.money-active {
            background: rgba(245, 158, 11, 0.2);
            border-color: var(--col-l1);
            color: #fde68a;
            box-shadow: 0 0 14px rgba(245, 158, 11, 0.4);
        }

        /* Main App Body Split */
        #app-container {
            flex: 1;
            display: flex;
            position: relative;
            overflow: hidden;
        }

        /* Left Sidebar: Forensic Intelligence Dossier */
        #sidebar-left {
            width: 320px;
            background: rgba(8, 14, 28, 0.96);
            border-right: 1px solid var(--border-subtle);
            display: flex;
            flex-direction: column;
            z-index: 40;
            backdrop-filter: blur(14px);
            transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1), transform 0.3s;
        }

        #sidebar-left.collapsed {
            transform: translateX(-320px);
            width: 0;
        }

        .sidebar-section {
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .sidebar-title {
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Recovery Metrics Breakdown */
        .metric-card-grid {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .metric-strip {
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            gap: 3px;
            position: relative;
            overflow: hidden;
        }

        .metric-strip::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 3px;
        }

        .strip-red::before { background: var(--col-victim); }
        .strip-green::before { background: var(--col-hold); }
        .strip-orange::before { background: var(--col-atm); }
        .strip-purple::before { background: var(--col-l3); }

        .strip-top {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--text-secondary);
        }

        .strip-amount {
            font-size: 15px;
            font-weight: 800;
            color: #ffffff;
            font-family: monospace;
        }

        /* Search Filter Input */
        .search-wrapper {
            position: relative;
            margin-bottom: 4px;
        }

        .search-wrapper input {
            width: 100%;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            padding: 8px 12px 8px 32px;
            font-size: 12px;
            color: #fff;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-wrapper input:focus {
            border-color: var(--col-cyan);
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.25);
        }

        .search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 12px;
            color: var(--text-muted);
        }

        /* Interactive Bank & Node Roster */
        .roster-list {
            flex: 1;
            overflow-y: auto;
            padding: 8px 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .roster-item {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            padding: 8px 10px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
        }

        .roster-item:hover {
            border-color: var(--col-cyan);
            background: rgba(0, 240, 255, 0.08);
            transform: translateX(4px);
        }

        .roster-info {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .roster-name {
            font-size: 12px;
            font-weight: 700;
            color: #ffffff;
        }

        .roster-sub {
            font-size: 10px;
            color: var(--text-muted);
            font-family: monospace;
        }

        .roster-badge {
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }

        /* Center 3D & Radial Viewport */
        #stage-viewport {
            flex: 1;
            position: relative;
            overflow: hidden;
            background: radial-gradient(circle at 50% 50%, #0a1122 0%, #030712 100%);
            perspective: 1200px;
            cursor: grab;
        }

        #stage-viewport:active {
            cursor: grabbing;
        }

        /* High-Tech Grid Flooring */
        .moving-grid-bg {
            position: absolute;
            width: 200%;
            height: 200%;
            left: -50%;
            top: -50%;
            background-size: 50px 50px;
            background-image: 
                linear-gradient(to right, rgba(255, 255, 255, 0.025) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
            pointer-events: none;
            transform: rotateX(60deg) translateZ(-200px);
            opacity: 0.8;
        }

        /* 3D World Scene */
        #world-3d {
            position: absolute;
            width: 1600px;
            height: 940px;
            top: 0;
            left: 0;
            transform-style: preserve-3d;
            transition: transform 0.1s linear;
        }

        /* SVG Cable Backbone & Orbital Rings Layer */
        #cables-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10;
        }

        /* Concentric Orbital Radar SVG Layer */
        #orbital-rings {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 5;
            transition: opacity 0.6s ease;
        }

        /* Canvas for 60 FPS Real-time Moving Money Packets */
        #motion-canvas {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 25;
        }

        /* 3D Layer Elevation Baseplates for Column View */
        .baseplate {
            position: absolute;
            border-radius: 18px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            transform-style: preserve-3d;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(4px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }

        .baseplate-tag {
            position: absolute;
            top: -24px;
            left: 16px;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            padding: 3px 10px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .plate-victim {
            width: 280px;
            height: 540px;
            left: 50px;
            top: 150px;
            border-color: rgba(239, 68, 68, 0.3);
            background: linear-gradient(180deg, rgba(239, 68, 68, 0.06) 0%, rgba(15, 23, 42, 0.4) 100%);
        }
        .plate-victim .baseplate-tag { background: rgba(239, 68, 68, 0.2); color: var(--col-victim); border: 1px solid var(--col-victim); }

        .plate-l1 {
            width: 280px;
            height: 600px;
            left: 360px;
            top: 40px;
            border-color: rgba(245, 158, 11, 0.3);
            background: linear-gradient(180deg, rgba(245, 158, 11, 0.06) 0%, rgba(15, 23, 42, 0.4) 100%);
        }
        .plate-l1 .baseplate-tag { background: rgba(245, 158, 11, 0.2); color: var(--col-l1); border: 1px solid var(--col-l1); }

        .plate-l2 {
            width: 280px;
            height: 520px;
            left: 670px;
            top: 100px;
            border-color: rgba(6, 182, 212, 0.3);
            background: linear-gradient(180deg, rgba(6, 182, 212, 0.06) 0%, rgba(15, 23, 42, 0.4) 100%);
        }
        .plate-l2 .baseplate-tag { background: rgba(6, 182, 212, 0.2); color: var(--col-l2); border: 1px solid var(--col-l2); }

        .plate-l3 {
            width: 290px;
            height: 640px;
            left: 1000px;
            top: 20px;
            border-color: rgba(168, 85, 247, 0.3);
            background: linear-gradient(180deg, rgba(168, 85, 247, 0.06) 0%, rgba(15, 23, 42, 0.4) 100%);
        }
        .plate-l3 .baseplate-tag { background: rgba(168, 85, 247, 0.2); color: var(--col-l3); border: 1px solid var(--col-l3); }

        /* Forensic Node Entity Cards */
        .forensic-card {
            position: absolute;
            width: 240px;
            background: var(--bg-card);
            border: 2px solid var(--border-subtle);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
            transform-style: preserve-3d;
            transition: left 0.75s cubic-bezier(0.16, 1, 0.3, 1), top 0.75s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.35s, border-color 0.35s, opacity 0.35s, transform 0.3s;
            cursor: pointer;
            backdrop-filter: blur(12px);
            z-index: 20;
        }

        .forensic-card:hover {
            transform: translateZ(28px) scale(1.03);
            z-index: 60;
        }

        /* Card Spotlight and Dim States */
        .forensic-card.dimmed {
            opacity: 0.18;
            filter: grayscale(85%) blur(1px);
        }

        .forensic-card.spotlight {
            opacity: 1;
            filter: none;
        }

        /* Entity Visual Types */
        .card-victim {
            border-color: rgba(239, 68, 68, 0.6);
            box-shadow: 0 0 25px rgba(239, 68, 68, 0.35);
        }
        .card-victim.victim-pulsing {
            animation: pulseVictim 2s infinite alternate;
        }
        @keyframes pulseVictim {
            0% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.4); }
            100% { box-shadow: 0 0 45px rgba(239, 68, 68, 0.85), 0 0 70px rgba(239, 68, 68, 0.3); }
        }

        .card-l1 {
            border-color: rgba(245, 158, 11, 0.6);
            box-shadow: 0 0 20px rgba(245, 158, 11, 0.25);
        }

        .card-l2 {
            border-color: rgba(6, 182, 212, 0.6);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.25);
        }

        .card-l3 {
            border-color: rgba(168, 85, 247, 0.6);
            box-shadow: 0 0 20px rgba(168, 85, 247, 0.25);
        }

        .card-hold {
            border-color: rgba(16, 185, 129, 0.8);
            box-shadow: 0 0 30px rgba(16, 185, 129, 0.4);
            animation: pulseHold 2.4s infinite alternate;
        }
        @keyframes pulseHold {
            0% { box-shadow: 0 0 20px rgba(16, 185, 129, 0.35); }
            100% { box-shadow: 0 0 45px rgba(16, 185, 129, 0.75); }
        }

        .card-atm {
            border-color: rgba(249, 115, 22, 0.8);
            box-shadow: 0 0 25px rgba(249, 115, 22, 0.4);
            animation: pulseAtm 1.8s infinite alternate;
        }
        @keyframes pulseAtm {
            0% { box-shadow: 0 0 15px rgba(249, 115, 22, 0.4); }
            100% { box-shadow: 0 0 35px rgba(249, 115, 22, 0.8); }
        }

        /* Card Interior Elements */
        .card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 6px;
            margin-bottom: 6px;
        }

        .badge-pill {
            font-size: 9px;
            font-weight: 800;
            padding: 2px 7px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border: 1px solid currentColor;
            background: rgba(255, 255, 255, 0.06);
        }

        .entity-icon {
            font-size: 15px;
        }

        .card-entity-title {
            font-size: 13px;
            font-weight: 800;
            color: #ffffff;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .card-entity-bank {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-top: 1px;
        }

        .card-entity-acc {
            font-size: 11px;
            font-family: monospace;
            color: var(--col-cyan);
            margin-top: 2px;
            letter-spacing: 0.5px;
        }

        .card-amount-panel {
            margin-top: 8px;
            padding-top: 6px;
            border-top: 1px dashed rgba(255, 255, 255, 0.12);
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }

        .amt-lbl {
            font-size: 9px;
            font-weight: 800;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        .amt-fig {
            font-size: 15px;
            font-weight: 900;
            font-feature-settings: "tnum";
            font-family: monospace;
        }

        .card-footer-alert {
            font-size: 9px;
            margin-top: 6px;
            padding: 3px 6px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.04);
            display: flex;
            align-items: center;
            gap: 5px;
            color: #cbd5e1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Bottom Step Controller & Playback Bar */
        #bottom-controller {
            background: linear-gradient(180deg, rgba(8, 14, 28, 0.96) 0%, #030712 100%);
            border-top: 1px solid var(--border-subtle);
            padding: 10px 24px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 50;
            backdrop-filter: blur(14px);
        }

        .narrative-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(0, 240, 255, 0.2);
            border-radius: 8px;
            padding: 8px 16px;
        }

        .narrative-main {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            color: #e2e8f0;
        }

        .step-index-badge {
            background: linear-gradient(135deg, #0284c7 0%, #00f0ff 100%);
            color: #030712;
            font-weight: 900;
            font-size: 10px;
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .narrative-sub-hindi {
            font-size: 12px;
            color: #94a3b8;
            font-style: italic;
        }

        .controller-tools-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .playback-buttons {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-step {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--border-subtle);
            color: var(--text-main);
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .btn-step:hover {
            border-color: var(--col-cyan);
            background: rgba(0, 240, 255, 0.15);
            color: #fff;
        }

        .btn-step.active {
            background: rgba(0, 240, 255, 0.25);
            border-color: var(--col-cyan);
            color: var(--col-cyan);
        }

        .stepper-timeline {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .stepper-btn {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }

        .stepper-btn.current {
            background: rgba(0, 240, 255, 0.2);
            border-color: var(--col-cyan);
            color: var(--col-cyan);
            box-shadow: 0 0 12px rgba(0, 240, 255, 0.35);
        }

        .camera-views {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Right Slide-over Forensic Inspector Drawer */
        #inspector-drawer {
            position: absolute;
            top: 0;
            right: 0;
            bottom: 0;
            width: 360px;
            background: rgba(8, 14, 28, 0.98);
            border-left: 1px solid rgba(0, 240, 255, 0.35);
            box-shadow: -10px 0 35px rgba(0, 0, 0, 0.8);
            z-index: 150;
            transform: translateX(100%);
            transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            padding: 20px;
            overflow-y: auto;
            backdrop-filter: blur(16px);
        }

        #inspector-drawer.open {
            transform: translateX(0);
        }

        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
            margin-bottom: 16px;
        }

        .drawer-title {
            font-size: 15px;
            font-weight: 800;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-close-drawer {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 20px;
            cursor: pointer;
        }
        .btn-close-drawer:hover { color: #fff; }

        .drawer-field {
            margin-bottom: 14px;
        }

        .df-label {
            font-size: 10px;
            font-weight: 800;
            text-transform: uppercase;
            color: var(--text-muted);
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }

        .df-value {
            font-size: 13px;
            color: #fff;
            font-weight: 600;
        }

        .df-copy-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .btn-copy {
            background: rgba(0, 240, 255, 0.12);
            border: 1px solid rgba(0, 240, 255, 0.3);
            color: var(--col-cyan);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            cursor: pointer;
        }
        .btn-copy:hover { background: rgba(0, 240, 255, 0.25); }

        .drawer-legal-advisory {
            background: rgba(245, 158, 11, 0.1);
            border: 1px solid rgba(245, 158, 11, 0.35);
            border-radius: 8px;
            padding: 12px;
            margin-top: 10px;
            font-size: 11px;
            color: #fde68a;
            line-height: 1.5;
        }

        /* Real-time Motion Telemetry Compass HUD */
        .stage-hud-compass {
            position: absolute;
            bottom: 16px;
            right: 20px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 11px;
            font-family: monospace;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 12px;
            pointer-events: none;
            z-index: 30;
        }

        .fps-badge {
            color: #10b981;
            font-weight: 800;
        }

        /* SVG Cable glow styles */
        .cable-shadow {
            stroke: rgba(0, 0, 0, 0.7);
            stroke-width: 6px;
            fill: none;
            stroke-linecap: round;
        }

        .cable-glow {
            stroke-width: 2.5px;
            fill: none;
            stroke-linecap: round;
            transition: stroke-dashoffset 0.1s linear, opacity 0.3s;
        }

        .cable-dash {
            stroke-dasharray: 6, 6;
            animation: cableMarch 1.2s linear infinite;
        }
        @keyframes cableMarch {
            from { stroke-dashoffset: 24; }
            to { stroke-dashoffset: 0; }
        }

        /* Circular Radar Sweep Keyframe */
        @keyframes radarRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>

    <!-- TOP HEADER BAR -->
    <header>
        <div class="header-brand">
            <div class="crest-wrapper">
                <svg viewBox="0 0 24 24">
                    <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 2.18l7 3.12v4.7c0 4.67-3.13 9.03-7 10.18-3.87-1.15-7-5.51-7-10.18V6.3l7-3.12zM12 6a4 4 0 100 8 4 4 0 000-8zm-2 4a2 2 0 114 0 2 2 0 01-4 0z"/>
                </svg>
            </div>
            <div class="brand-meta">
                <h1>
                    <span>FORENSIC MONEY TRAIL 3D RADAR ENGINE</span>
                    <span class="live-tag"><span class="pulse-dot"></span> LIVE FRAUD STREAM</span>
                </h1>
                <p>
                    <span>FIR No: <b>281/2026</b> PS Cyber North</span>
                    <span class="meta-chip">NCRP ACK: 30809260089905</span>
                    <span class="meta-chip">VICTIM: AMIT KUMAR (₹1,98,000)</span>
                    <span class="meta-chip" style="color: var(--col-hold); border-color: var(--col-hold);">TOTAL LIEN HELD: ₹1,16,917.10 (59.05%)</span>
                </p>
            </div>
        </div>

        <!-- 1-CLICK DUAL LAYOUT SWITCHER -->
        <div class="layout-switcher">
            <button class="btn-layout active" id="btn-layout-circular" onclick="switchLayoutMode('circular')">
                ⭕ Circular Orbit View (सर्कल व्यू)
            </button>
            <button class="btn-layout" id="btn-layout-columns" onclick="switchLayoutMode('columns')">
                📐 3D Columns View (कॉलम व्यू)
            </button>
        </div>

        <!-- Right Quick Action Tools -->
        <div class="header-actions">
            <button class="btn-act money-active" id="btn-toggle-money" onclick="toggleMoneyStream()">💸 Money Stream: ON</button>
            <button class="btn-act active-glow" id="btn-cinematic" onclick="toggleCinematicCamera()">🎥 Cinematic Orbit: ON</button>
            <button class="btn-act" onclick="replayVictimBurst()">💥 Replay Burst</button>
            <button class="btn-act" onclick="toggleSidebar()">📁 Dossier Panel</button>
            <button class="btn-act" id="lang-indicator" onclick="toggleLanguage()">🌐 EN / हिन्दी</button>
        </div>
    </header>

    <!-- MAIN APP CONTAINER -->
    <div id="app-container">
        <!-- LEFT FORENSIC DOSSIER SIDEBAR -->
        <aside id="sidebar-left">
            <div class="sidebar-section">
                <div class="sidebar-title">
                    <span>FINANCIAL RECOVERY DOSSIER</span>
                    <span style="color: var(--col-cyan);">BNSS SEC 94/106</span>
                </div>
                <div class="metric-card-grid">
                    <div class="metric-strip strip-red">
                        <div class="strip-top"><span>Total Disputed Inflow</span><span>3 Txns</span></div>
                        <div class="strip-amount" style="color: var(--col-victim);">₹1,98,000.00</div>
                    </div>
                    <div class="metric-strip strip-green">
                        <div class="strip-top"><span>Secured Under Lien / Hold</span><span>59.05%</span></div>
                        <div class="strip-amount" style="color: var(--col-hold);">₹1,16,917.10</div>
                    </div>
                    <div class="metric-strip strip-orange">
                        <div class="strip-top"><span>ATM Cash Leakage Siphoned</span><span>2 Switch Endpoints</span></div>
                        <div class="strip-amount" style="color: var(--col-atm);">₹77,082.90</div>
                    </div>
                    <div class="metric-strip strip-purple">
                        <div class="strip-top"><span>Merchant Gateway Captured</span><span>Meta Verified</span></div>
                        <div class="strip-amount" style="color: var(--col-l3);">₹4,000.00</div>
                    </div>
                </div>
            </div>

            <!-- Search Bank / Mule Node -->
            <div class="sidebar-section">
                <div class="sidebar-title"><span>SEARCH TRAIL ENTITIES</span></div>
                <div class="search-wrapper">
                    <span class="search-icon">🔍</span>
                    <input type="text" id="node-search" placeholder="Search Bank, Account, UTR, Role..." oninput="handleSearch(this.value)">
                </div>
            </div>

            <!-- Entities Roster List -->
            <div class="sidebar-title" style="padding: 10px 16px 0;"><span>TRAIL ENTITIES (10 NODES)</span></div>
            <div class="roster-list" id="roster-container">
                <!-- Dynamically populated by JS -->
            </div>

            <!-- Real-time Speed Controller -->
            <div class="sidebar-section" style="margin-top: auto;">
                <div class="sidebar-title">
                    <span>MONEY FLOW VELOCITY</span>
                    <span id="speed-label" style="color: var(--col-gold);">1.0x Normal</span>
                </div>
                <div style="display: flex; gap: 6px;">
                    <button class="btn-step" style="flex: 1;" onclick="setStreamSpeed(0.5)">0.5x Slow</button>
                    <button class="btn-step active-glow" id="speed-normal" style="flex: 1;" onclick="setStreamSpeed(1.0)">1.0x</button>
                    <button class="btn-step" style="flex: 1;" onclick="setStreamSpeed(2.0)">2.0x Fast</button>
                </div>
            </div>
        </aside>

        <!-- CENTER 3D VIEWPORT -->
        <main id="stage-viewport">
            <div class="moving-grid-bg"></div>

            <div id="world-3d">
                <!-- 1. Concentric Orbital Rings SVG (Visible in Circular View) -->
                <svg id="orbital-rings">
                    <defs>
                        <!-- Radial Radar Glow Gradient -->
                        <radialGradient id="victimCoreGlow" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stop-color="#ef4444" stop-opacity="0.25"/>
                            <stop offset="60%" stop-color="#ef4444" stop-opacity="0.08"/>
                            <stop offset="100%" stop-color="#ef4444" stop-opacity="0"/>
                        </radialGradient>

                        <!-- Conical Radar Sweep Sweep -->
                        <linearGradient id="sweepGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.35"/>
                            <stop offset="50%" stop-color="#00f0ff" stop-opacity="0.08"/>
                            <stop offset="100%" stop-color="#00f0ff" stop-opacity="0"/>
                        </linearGradient>
                    </defs>

                    <!-- Center Victim Core Aura -->
                    <circle cx="800" cy="460" r="140" fill="url(#victimCoreGlow)" />
                    <circle cx="800" cy="460" r="90" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4, 4" opacity="0.4"/>

                    <!-- ORBIT 1: Layer 1 Entry Mules (Rx=270, Ry=190) -->
                    <ellipse cx="800" cy="460" rx="270" ry="190" fill="none" stroke="#00f0ff" stroke-width="1.5" stroke-dasharray="8, 6" opacity="0.35"/>
                    <text x="800" y="255" fill="#00f0ff" font-size="10" font-weight="800" letter-spacing="1" text-anchor="middle" opacity="0.75">[ ORBIT 1: LAYER 1 ENTRY MULE CLUSTER • RADIUS 270px ]</text>

                    <!-- ORBIT 2: Layer 2 Propagation (Rx=475, Ry=290) -->
                    <ellipse cx="800" cy="460" rx="475" ry="290" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="10, 8" opacity="0.35"/>
                    <text x="800" y="155" fill="#f59e0b" font-size="10" font-weight="800" letter-spacing="1" text-anchor="middle" opacity="0.75">[ ORBIT 2: LAYER 2 ROUTING & INTERMEDIATE HOPS • RADIUS 475px ]</text>

                    <!-- ORBIT 3: Terminal Outflow & Lien (Rx=660, Ry=385) -->
                    <ellipse cx="800" cy="460" rx="660" ry="385" fill="none" stroke="#a855f7" stroke-width="1.5" stroke-dasharray="12, 10" opacity="0.35"/>
                    <text x="800" y="60" fill="#a855f7" font-size="10" font-weight="800" letter-spacing="1" text-anchor="middle" opacity="0.75">[ ORBIT 3: TERMINAL ATM CASH-OUTS & LIEN MARKED ASSETS • RADIUS 660px ]</text>

                    <!-- Crosshairs & Cardinal Degree Coordinates -->
                    <line x1="800" y1="50" x2="800" y2="870" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="4, 4"/>
                    <line x1="120" y1="460" x2="1480" y2="460" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="4, 4"/>
                    <text x="800" y="35" fill="#64748b" font-size="9" font-family="monospace" text-anchor="middle">000° NORTH (AZIMUTH)</text>
                    <text x="1500" y="464" fill="#64748b" font-size="9" font-family="monospace">090° EAST</text>
                    <text x="800" y="890" fill="#64748b" font-size="9" font-family="monospace" text-anchor="middle">180° SOUTH</text>
                    <text x="50" y="464" fill="#64748b" font-size="9" font-family="monospace">270° WEST</text>

                    <!-- Rotating Radar Scanner Sweep -->
                    <g style="transform-origin: 800px 460px; animation: radarRotate 12s linear infinite;">
                        <path d="M 800 460 L 1460 460 A 660 385 0 0 0 1340 220 Z" fill="url(#sweepGrad)"/>
                        <line x1="800" y1="460" x2="1460" y2="460" stroke="#00f0ff" stroke-width="2" opacity="0.8"/>
                    </g>
                </svg>

                <!-- 2. SVG Static Cables Backbone -->
                <svg id="cables-canvas"></svg>

                <!-- 3. Canvas for Moving Money Packets -->
                <canvas id="motion-canvas" width="1600" height="940"></canvas>

                <!-- 4. 3D Layer Elevation Baseplates (Column Mode) -->
                <div class="baseplate plate-victim" id="baseplate-0">
                    <span class="baseplate-tag">Layer 0 • Victim Core</span>
                </div>
                <div class="baseplate plate-l1" id="baseplate-1">
                    <span class="baseplate-tag">Layer 1 • Entry Disbursal</span>
                </div>
                <div class="baseplate plate-l2" id="baseplate-2">
                    <span class="baseplate-tag">Layer 2 • Propagation</span>
                </div>
                <div class="baseplate plate-l3" id="baseplate-3">
                    <span class="baseplate-tag">Layer 3 • Cash-Out & Lien</span>
                </div>

                <!-- 5. FORENSIC NODE CARDS (10 NODES) -->
                <!-- NODE 1: Victim Complainant (Central Core) -->
                <div class="forensic-card card-victim victim-pulsing" id="card-victim" onclick="openInspector('victim')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-victim); background: rgba(239,68,68,0.25);">Layer 0 • Complainant</span>
                        <span class="entity-icon">👤</span>
                    </div>
                    <div class="card-entity-title">AMIT KUMAR (Victim)</div>
                    <div class="card-entity-bank">Union Bank of India</div>
                    <div class="card-entity-acc">A/c: 125910100019333</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Total Siphoned</span>
                        <span class="amt-fig" style="color: var(--col-victim);">₹1,98,000.00</span>
                    </div>
                    <div class="card-footer-alert">🚨 3 Unauthorized Fraud UPI Debits</div>
                </div>

                <!-- NODE 2: Indian Overseas Bank (Layer 1 Mule) -->
                <div class="forensic-card card-l1" id="card-iob" onclick="openInspector('iob')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-l1); background: rgba(245,158,11,0.25);">Layer 1 • Entry Mule</span>
                        <span class="entity-icon">🏦</span>
                    </div>
                    <div class="card-entity-title">Indian Overseas Bank Mule</div>
                    <div class="card-entity-bank">IFSC: IOBA0000499</div>
                    <div class="card-entity-acc">A/c: 049901000021812</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Transferred Inflow</span>
                        <span class="amt-fig" style="color: var(--col-l1);">₹99,000.00</span>
                    </div>
                    <div class="card-footer-alert">⚠️ Siphoned to ATM (₹76.5K) & Hold (₹21.9K)</div>
                </div>

                <!-- NODE 3: IDFC First Bank (Layer 1 100% Full Lien) -->
                <div class="forensic-card card-hold" id="card-idfc" onclick="openInspector('idfc')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-hold); background: rgba(16,185,129,0.25);">Layer 1 • 100% Lien</span>
                        <span class="entity-icon">🛡️</span>
                    </div>
                    <div class="card-entity-title">IDFC First Bank Mule</div>
                    <div class="card-entity-bank">IFSC: IDFB0000000</div>
                    <div class="card-entity-acc">A/c: 10304040490</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">100% Full Freeze</span>
                        <span class="amt-fig" style="color: var(--col-hold);">₹95,000.00</span>
                    </div>
                    <div class="card-footer-alert">🔒 Entire Fraud Amount Secured</div>
                </div>

                <!-- NODE 4: ICICI Bank Payment Gateway Transit -->
                <div class="forensic-card card-l1" id="card-icici" onclick="openInspector('icici')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-l1); background: rgba(245,158,11,0.25);">Layer 1 • PG Transit</span>
                        <span class="entity-icon">💳</span>
                    </div>
                    <div class="card-entity-title">ICICI Bank Gateway Hop</div>
                    <div class="card-entity-bank">IFSC: ICIC0DC0099</div>
                    <div class="card-entity-acc">A/c: 0103SL00IPAY</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Routed Volume</span>
                        <span class="amt-fig" style="color: var(--col-l1);">₹4,000.00</span>
                    </div>
                    <div class="card-footer-alert">⚡ Dispatched to PayU Aggregator</div>
                </div>

                <!-- NODE 5: State Bank of India (Layer 2 Mule) -->
                <div class="forensic-card card-l2" id="card-sbi" onclick="openInspector('sbi')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-l2); background: rgba(6,182,212,0.25);">Layer 2 • Mule</span>
                        <span class="entity-icon">🏦</span>
                    </div>
                    <div class="card-entity-title">State Bank of India Mule</div>
                    <div class="card-entity-bank">IFSC: SBIN0001883</div>
                    <div class="card-entity-acc">A/c: 00000042581502450</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Received from IOB</span>
                        <span class="amt-fig" style="color: var(--col-l2);">₹500.00</span>
                    </div>
                    <div class="card-footer-alert">🏧 Rapid ATM Cash Withdrawal</div>
                </div>

                <!-- NODE 6: PayU Payments Aggregator (Layer 2 Gateway) -->
                <div class="forensic-card card-l2" id="card-payu" onclick="openInspector('payu')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-l2); background: rgba(6,182,212,0.25);">Layer 2 • Aggregator</span>
                        <span class="entity-icon">📱</span>
                    </div>
                    <div class="card-entity-title">PayU Payments Pvt Ltd</div>
                    <div class="card-entity-bank">VPA: facebookadsmanager.payu</div>
                    <div class="card-entity-acc">Virtual Transit Node</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Aggregated</span>
                        <span class="amt-fig" style="color: var(--col-l2);">₹4,000.00</span>
                    </div>
                    <div class="card-footer-alert">➡️ Settled to Citi Bank Meta Verified</div>
                </div>

                <!-- NODE 7: IOB Put on Hold (Lien Marked Asset) -->
                <div class="forensic-card card-hold" id="card-iob-hold" onclick="openInspector('iob_hold')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-hold); background: rgba(16,185,129,0.3);">🛡️ Lien Put On Hold</span>
                        <span class="entity-icon">🔒</span>
                    </div>
                    <div class="card-entity-title">IOB Lien Marked Asset</div>
                    <div class="card-entity-bank">Indian Overseas Bank</div>
                    <div class="card-entity-acc">A/c: 049901000021812</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Frozen & Secured</span>
                        <span class="amt-fig" style="color: var(--col-hold);">₹21,917.10</span>
                    </div>
                    <div class="card-footer-alert">✅ Remaining Balance Zeroed (Frozen)</div>
                </div>

                <!-- NODE 8: IOB Mule ATM Cash Withdrawal -->
                <div class="forensic-card card-atm" id="card-iob-atm" onclick="openInspector('iob_atm')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-atm); background: rgba(249,115,22,0.3);">🏧 ATM Cash-Out</span>
                        <span class="entity-icon">💸</span>
                    </div>
                    <div class="card-entity-title">IOB Mule ATM Cash-Out</div>
                    <div class="card-entity-bank">IOB Terminal Switch</div>
                    <div class="card-entity-acc">Source: 049901000021812</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Cash Withdrawn</span>
                        <span class="amt-fig" style="color: var(--col-atm);">₹76,582.90</span>
                    </div>
                    <div class="card-footer-alert">🚨 ATM CCTV Requisition Sent (Sec 94)</div>
                </div>

                <!-- NODE 9: SBI Mule ATM Cash Withdrawal -->
                <div class="forensic-card card-atm" id="card-sbi-atm" onclick="openInspector('sbi_atm')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-atm); background: rgba(249,115,22,0.3);">🏧 ATM Cash-Out</span>
                        <span class="entity-icon">💸</span>
                    </div>
                    <div class="card-entity-title">SBI Mule ATM Cash-Out</div>
                    <div class="card-entity-bank">SBI ATM Terminal</div>
                    <div class="card-entity-acc">Source: 00000042581502450</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Cash Withdrawn</span>
                        <span class="amt-fig" style="color: var(--col-atm);">₹500.00</span>
                    </div>
                    <div class="card-footer-alert">🚨 Micro Cash Extraction via ATM</div>
                </div>

                <!-- NODE 10: Citi Bank Meta Verified (Layer 3 Terminal Merchant) -->
                <div class="forensic-card card-l3" id="card-citi" onclick="openInspector('citi')">
                    <div class="card-head">
                        <span class="badge-pill" style="border-color: var(--col-l3); background: rgba(168,85,247,0.25);">Layer 3 • Merchant</span>
                        <span class="entity-icon">🛍️</span>
                    </div>
                    <div class="card-entity-title">Citi Bank / Meta Verified</div>
                    <div class="card-entity-bank">IFSC: CITI0000006</div>
                    <div class="card-entity-acc">A/c: 521752076</div>
                    <div class="card-amount-panel">
                        <span class="amt-lbl">Settled Volume</span>
                        <span class="amt-fig" style="color: var(--col-l3);">₹4,000.00</span>
                    </div>
                    <div class="card-footer-alert">✅ Merchant Captured (Meta Verified)</div>
                </div>

            </div>

            <!-- Real-time Motion Telemetry HUD on Bottom Right -->
            <div class="stage-hud-compass">
                <span>FPS: <b class="fps-badge" id="fps-counter">60</b></span>
                <span>•</span>
                <span id="motion-mode-text" style="color: var(--col-cyan);">⭕ Circular Orbit Active</span>
                <span>•</span>
                <span>Moving Money Streams: <b style="color: #fbbf24;" id="active-streams-count">3 Active</b></span>
            </div>
        </main>
    </div>

    <!-- BOTTOM STEP CONTROLLER & NARRATIVE BAR -->
    <div id="bottom-controller">
        <!-- Live Narrative Bar -->
        <div class="narrative-row">
            <div class="narrative-main">
                <span class="step-index-badge" id="step-badge-text">STEP 1 / 5</span>
                <span id="narrative-english" style="font-weight: 600;">Victim Amit Kumar was defrauded of ₹1,98,000 via 3 unauthorized UPI debits moving to Layer 1 accounts.</span>
            </div>
            <div class="narrative-sub-hindi" id="narrative-hindi">
                पीड़ित अमित कुमार के खाते से 3 यूपीआई ट्रांजेक्शन के जरिए ₹1,98,000 की ठगी कर लेयर 1 में भेजी गई।
            </div>
        </div>

        <!-- Playback Controller Tools -->
        <div class="controller-tools-row">
            <div class="playback-buttons">
                <button class="btn-step" onclick="jumpToStep(1)">⏮ Reset</button>
                <button class="btn-step" onclick="stepPrevious()">◀ Prev</button>
                <button class="btn-step" id="btn-play-pause" onclick="toggleAutoPlay()">⏵ Auto Play</button>
                <button class="btn-step" onclick="stepNext()">Next ▶</button>
                <button class="btn-step" onclick="showCompleteTrail()">👁 Show Full Trail</button>
            </div>

            <div class="stepper-timeline">
                <button class="stepper-btn current" id="step-btn-1" onclick="jumpToStep(1)">1. Fraud Debits</button>
                <button class="stepper-btn" id="step-btn-2" onclick="jumpToStep(2)">2. Lien Holds (₹1.16L)</button>
                <button class="stepper-btn" id="step-btn-3" onclick="jumpToStep(3)">3. Layer 2 Mules & PG</button>
                <button class="stepper-btn" id="step-btn-4" onclick="jumpToStep(4)">4. ATM Cash-Outs</button>
                <button class="stepper-btn" id="step-btn-5" onclick="jumpToStep(5)">5. Master Trail</button>
            </div>

            <div class="camera-views">
                <button class="btn-step" onclick="switchCamera('iso')">🎮 3D Orbit</button>
                <button class="btn-step" onclick="switchCamera('top')">📐 2D Flowchart</button>
                <button class="btn-step" onclick="switchCamera('deep')">🔍 Deep 3D</button>
            </div>
        </div>
    </div>

    <!-- RIGHT SLIDE-OVER FORENSIC INSPECTOR DRAWER -->
    <div id="inspector-drawer">
        <div class="drawer-header">
            <div class="drawer-title">
                <span id="ins-icon">🛡️</span>
                <span id="ins-title">Entity Dossier</span>
            </div>
            <button class="btn-close-drawer" onclick="closeInspector()">×</button>
        </div>

        <div class="drawer-field">
            <div class="df-label">Entity Title / Role</div>
            <div class="df-value" id="ins-name">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-label">Banking Institution & IFSC</div>
            <div class="df-value" id="ins-bank">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-copy-row">
                <div class="df-label">Account No / Virtual VPA</div>
                <button class="btn-copy" onclick="copyAccountNo()">📋 Copy</button>
            </div>
            <div class="df-value" id="ins-acc" style="color: var(--col-cyan); font-family: monospace; font-size: 14px;">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-label">Transaction UTR / IMPS Ref</div>
            <div class="df-value" id="ins-utr" style="font-family: monospace;">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-label">Forensic Layer & Classification</div>
            <div class="df-value" id="ins-layer">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-label">Disputed / Transaction Volume</div>
            <div class="df-value" id="ins-amt" style="font-size: 18px; font-weight: 900;">-</div>
        </div>

        <div class="drawer-field">
            <div class="df-label">Action Taken / Asset Disposition</div>
            <div class="df-value" id="ins-action">-</div>
        </div>

        <div class="drawer-legal-advisory" id="ins-legal">
            <b>Statutory Legal Power (BNSS):</b><br>
            Notice under Section 94 BNSS issued for production of account KYC, switch IP logs, ATM surveillance video recordings, and transaction trail. Section 106 BNSS invoked for immediate attachment and seizure of defrauded balances.
        </div>
    </div>

    <!-- JAVASCRIPT REAL-TIME CIRCULAR & 3D MOTION ENGINE -->
    <script>
        // Entity Registry Data
        const ENTITY_REGISTRY = {
            victim: {
                id: "card-victim", icon: "👤", title: "Victim (Complainant)",
                name: "AMIT KUMAR (Mobile: +91-8287672197)", bank: "Union Bank of India",
                acc: "125910100019333", utr: "3 UPI Debits: 627114473693, 627215014158, 627216047641",
                layer: "Layer 0 • Complainant Account", amt: "₹1,98,000.00 (Total Disputed)",
                action: "NCRP Acknowledgment: 30809260089905 | Case FIR No. 281/2026 registered at Cyber PS North District.",
                color: "#ef4444"
            },
            iob: {
                id: "card-iob", icon: "🏦", title: "Layer 1 Mule Account",
                name: "Indian Overseas Bank Beneficiary", bank: "Indian Overseas Bank (IFSC: IOBA0000499)",
                acc: "049901000021812", utr: "Txn ID: 627114473693 (28/09/2026 14:36 PM)",
                layer: "Layer 1 • Entry Disbursal Mule", amt: "₹99,000.00 Credited",
                action: "Partial Lien Marked: ₹21,917.10. Siphoned via ATM: ₹76,582.90. Transferred to SBI: ₹500.00.",
                color: "#f59e0b"
            },
            idfc: {
                id: "card-idfc", icon: "🛡️", title: "Layer 1 Mule (100% Full Lien)",
                name: "IDFC First Bank Beneficiary", bank: "IDFC First Bank (IFSC: IDFB0000000)",
                acc: "10304040490", utr: "Txn ID: 627215014158 (29/09/2026 15:31 PM)",
                layer: "Layer 1 • 100% Secured Mule Account", amt: "₹95,000.00 (100% Lien Marked)",
                action: "Full Debit Freeze marked on 29/09/2026 17:44:01. Complete available balance of ₹95,012.00 secured.",
                color: "#10b981"
            },
            icici: {
                id: "card-icici", icon: "💳", title: "Layer 1 Gateway Transit",
                name: "ICICI Bank Transit Account", bank: "ICICI Bank (IFSC: ICIC0DC0099)",
                acc: "0103SL00IPAY", utr: "Txn ID: 627216047641 (29/09/2026 16:42 PM)",
                layer: "Layer 1 • Payment Gateway Transit Hop", amt: "₹4,000.00 Credited",
                action: "Immediately routed into PayU Payments Private Limited gateway for Facebook Ads Manager.",
                color: "#a855f7"
            },
            sbi: {
                id: "card-sbi", icon: "🏦", title: "Layer 2 Mule Account",
                name: "State Bank of India Beneficiary", bank: "State Bank of India (IFSC: SBIN0001883)",
                acc: "00000042581502450", utr: "Txn ID: 627100238476 (28/09/2026 14:52 PM)",
                layer: "Layer 2 • Secondary Mule Account", amt: "₹500.00 Credited",
                action: "Received from IOB mule account; completely siphoned via ATM cash withdrawal.",
                color: "#06b6d4"
            },
            payu: {
                id: "card-payu", icon: "📱", title: "Layer 2 Payment Aggregator",
                name: "PayU Payments Private Limited", bank: "Virtual Aggregator (VPA: facebookadsmanager.payu@icici)",
                acc: "0103SL00IPAY", utr: "Txn ID: 627216047641",
                layer: "Layer 2 • Merchant Payment Aggregator", amt: "₹4,000.00 Aggregated",
                action: "Payment aggregated for merchant Meta Verified under Citi Bank settlement.",
                color: "#a855f7"
            },
            iob_hold: {
                id: "card-iob-hold", icon: "🔒", title: "Lien Marked Asset (IOB)",
                name: "Indian Overseas Bank Lien Amount", bank: "Indian Overseas Bank (A/c 049901000021812)",
                acc: "049901000021812", utr: "Lien Timestamp: 28/09/2026 17:44:01",
                layer: "Put On Hold • Secured Asset", amt: "₹21,917.10 (Frozen in Bank)",
                action: "Lien enforced on portal. Remaining balance reduced to zero. Secured for court disposal.",
                color: "#10b981"
            },
            iob_atm: {
                id: "card-iob-atm", icon: "💸", title: "ATM Cash Withdrawal (IOB)",
                name: "IOB Mule ATM Cash Siphoning", bank: "Indian Overseas Bank Switch",
                acc: "049901000021812", utr: "Cash debit prior to debit freeze",
                layer: "ATM Cash-Out Endpoint", amt: "₹76,582.90 Siphoned in Cash",
                action: "Withdrawn in cash via ATM terminal before lien. Section 94 BNSS notice issued for ATM CCTV footage.",
                color: "#f97316"
            },
            sbi_atm: {
                id: "card-sbi-atm", icon: "💸", title: "ATM Cash Withdrawal (SBI)",
                name: "SBI Mule ATM Cash Siphoning", bank: "State Bank of India ATM Switch",
                acc: "00000042581502450", utr: "ATM Cash Debit",
                layer: "ATM Cash-Out Endpoint", amt: "₹500.00 Siphoned in Cash",
                action: "Fast cash withdrawal via ATM terminal. Section 94 BNSS notice issued for CCTV recordings.",
                color: "#f97316"
            },
            citi: {
                id: "card-citi", icon: "🛍️", title: "Layer 3 Merchant Settlement",
                name: "Citi Bank / Meta Verified", bank: "Citi Bank (IFSC: CITI0000006)",
                acc: "521752076", utr: "UTR: 28804357342583915 (UPI Mode)",
                layer: "Layer 3 • Merchant Settlement Node", amt: "₹4,000.00 Settled",
                action: "Merchant: Meta Verified (Nodal Email: salilmody@fb.com). Status: Captured.",
                color: "#a855f7"
            }
        };

        // Dual Layout Coordinate Matrix
        const LAYOUT_COORDINATES = {
            circular: {
                "card-victim":   { left: 680, top: 395 },
                "card-icici":    { left: 820, top: 238 },
                "card-idfc":     { left: 886, top: 559 },
                "card-iob":      { left: 415, top: 395 },
                "card-payu":     { left: 1101, top: 244 },
                "card-iob-hold": { left: 389, top: 617 },
                "card-sbi":      { left: 360, top: 205 },
                "card-citi":     { left: 1345, top: 460 },
                "card-iob-atm":  { left: 25, top: 395 },
                "card-sbi-atm":  { left: 466, top: 41 }
            },
            columns: {
                "card-victim":   { left: 70, top: 280 },
                "card-iob":      { left: 380, top: 80 },
                "card-idfc":     { left: 380, top: 270 },
                "card-icici":    { left: 380, top: 460 },
                "card-sbi":      { left: 690, top: 140 },
                "card-payu":     { left: 690, top: 410 },
                "card-iob-hold": { left: 1020, top: 60 },
                "card-iob-atm":  { left: 1020, top: 215 },
                "card-sbi-atm":  { left: 1020, top: 370 },
                "card-citi":     { left: 1020, top: 525 }
            }
        };

        // Connecting Cable Links with Exact Moving Money Badges
        const CABLE_LINKS = [
            // STEP 1: Victim Outflow (Fraud Money in Motion)
            { id: "c_v_iob", from: "card-victim", to: "card-iob", color: "#f59e0b", step: 1, moneyText: "💸 ₹99,000", density: 2, speed: 0.22, isVictim: true },
            { id: "c_v_idfc", from: "card-victim", to: "card-idfc", color: "#10b981", step: 1, moneyText: "💸 ₹95,000", density: 2, speed: 0.22, isVictim: true },
            { id: "c_v_icici", from: "card-victim", to: "card-icici", color: "#a855f7", step: 1, moneyText: "💸 ₹4,000", density: 2, speed: 0.26, isVictim: true },
            
            // STEP 2: Emergency Lien Marking
            { id: "c_iob_hold", from: "card-iob", to: "card-iob-hold", color: "#10b981", step: 2, moneyText: "🔒 ₹21,917.10", density: 2, speed: 0.24, isVictim: false },
            
            // STEP 3: Layer 2 Propagation
            { id: "c_iob_sbi", from: "card-iob", to: "card-sbi", color: "#06b6d4", step: 3, moneyText: "💸 ₹500", density: 2, speed: 0.25, isVictim: false },
            { id: "c_icici_payu", from: "card-icici", to: "card-payu", color: "#a855f7", step: 3, moneyText: "📱 ₹4,000", density: 2, speed: 0.25, isVictim: false },
            
            // STEP 4: ATM Cash-Outs & Merchant Settlement
            { id: "c_iob_atm", from: "card-iob", to: "card-iob-atm", color: "#f97316", step: 4, moneyText: "🏧 ₹76,582.90", density: 2, speed: 0.28, isVictim: false },
            { id: "c_sbi_atm", from: "card-sbi", to: "card-sbi-atm", color: "#f97316", step: 4, moneyText: "🏧 ₹500", density: 2, speed: 0.28, isVictim: false },
            { id: "c_payu_citi", from: "card-payu", to: "card-citi", color: "#a855f7", step: 4, moneyText: "🛍️ ₹4,000", density: 2, speed: 0.25, isVictim: false }
        ];

        // Step Stories
        const STEP_STORIES = {
            1: {
                badge: "STEP 1 / 5 • INITIAL FRAUD DEBITS (VICTIM MONEY MOVING)",
                en: "Victim Amit Kumar was defrauded of ₹1,98,000. Watch the 3 fraudulent money packets moving from Union Bank into Layer 1: IOB (₹99,000), IDFC (₹95,000), and ICICI (₹4,000).",
                hi: "पीड़ित अमित कुमार के खाते से ₹1,98,000 की फ्रॉड राशि चलती हुई देखें — 3 पैकेट्स लेयर 1 के खातों (आईओबी ₹99,000, आईडीएफसी ₹95,000, आईसीआईसीआई ₹4,000) में ट्रांसफर हो रहे हैं।"
            },
            2: {
                badge: "STEP 2 / 5 • RAPID LIEN MARKING (HOLD)",
                en: "Emergency Police intervention & NCRP portal triggers: IDFC First Bank marked 100% full debit freeze of ₹95,000.00. Indian Overseas Bank marked partial lien of ₹21,917.10. Total secured: ₹1,16,917.10 (59.05%).",
                hi: "त्वरित कार्रवाई: आईडीएफसी बैंक में शत-प्रतिशत ₹95,000 और इंडियन ओवरसीज बैंक में ₹21,917.10 पर लीन (डेबिट फ्रीज) लगाया गया। कुल ₹1,16,917.10 (59.05%) सुरक्षित किए गए।"
            },
            3: {
                badge: "STEP 3 / 5 • LAYER 2 MULES & GATEWAY HOP",
                en: "Unfrozen active funds dispersed into Layer 2: ₹500 transferred from IOB to State Bank of India mule account (00000042581502450); ₹4,000 routed through PayU Payments Pvt Ltd gateway for Meta Ads.",
                hi: "शेष राशि लेयर 2 में भेजी गई: ₹500 आईओबी से एसबीआई म्यूल खाते में तथा ₹4,000 आईसीआईसीआई से पेयू गेटवे के माध्यम से ट्रांसफर किए गए।"
            },
            4: {
                badge: "STEP 4 / 5 • ATM CASH-OUTS & TERMINAL SETTLEMENT",
                en: "Syndicate cash leakages: ₹76,582.90 withdrawn in cash from IOB mule account via ATM; ₹500 withdrawn from SBI ATM; ₹4,000 settled with Meta Verified under Citi Bank account 521752076.",
                hi: "टर्मिनल निकासी: आईओबी म्यूल खाते से एटीएम द्वारा ₹76,582.90 और एसबीआई खाते से ₹500 नकद निकाले गए। पेयू के जरिए ₹4,000 मेटा वेरिफाइड (सिटी बैंक) द्वारा कैप्चर किए गए।"
            },
            5: {
                badge: "STEP 5 / 5 • COMPLETE MASTER TRAIL & RECOVERY MATRIX",
                en: "Complete forensic money trail mapped across 4 layers from Victim to all Mule accounts, ATM cash leakages, and Merchant endpoints. 59.05% (₹1,16,917.10) secured under lien. Statutory Section 94 & 106 BNSS notices issued.",
                hi: "पीड़ित से लेकर सभी म्यूल खातों, एटीएम और मर्चेंट तक पूरी मनी ट्रेल 4 लेयर्स में तैयार। ₹1,16,917.10 (59.05%) लीन में सुरक्षित। बीएनएसएस धारा 94 और 106 के नोटिस जारी।"
            }
        };

        // App & Motion State
        let currentLayout = 'circular'; // 'circular' or 'columns'
        let activeStep = 1;
        let isAutoPlay = false;
        let autoPlayTimer = null;
        let isCinematic = true;
        let isMoneyStreamRunning = true;
        let streamSpeed = 1.0;
        let activeLang = 'en';

        // 3D Camera Variables
        let rotX = 14;
        let rotY = -8;
        let baseRotX = 14;
        let baseRotY = -8;
        let zoom = 0.95;
        let panX = 30;
        let panY = -10;
        let isDragging = false;
        let lastX = 0, lastY = 0;
        let userInteracting = false;
        let idleTimer = null;

        // FPS & Timing Tracker
        let lastTimestamp = performance.now();
        let frameCount = 0;
        let lastFpsUpdate = performance.now();
        let globalMoneyTime = 0;

        // Canvas & DOM
        const world = document.getElementById("world-3d");
        const viewport = document.getElementById("stage-viewport");
        const cablesCanvas = document.getElementById("cables-canvas");
        const motionCanvas = document.getElementById("motion-canvas");
        const orbitalRings = document.getElementById("orbital-rings");
        const mCtx = motionCanvas.getContext("2d");

        // Shockwaves container
        const shockwaves = [];

        // Apply 3D Camera
        function applyCameraTransform() {
            world.style.transform = `translate3d(${panX}px, ${panY}px, 0) scale(${zoom}) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
        }

        function switchCamera(mode) {
            isCinematic = false;
            updateCinematicButtonUI();
            if (mode === 'iso') {
                rotX = 22; rotY = -14; zoom = 0.95; panX = 40; panY = -10;
            } else if (mode === 'top') {
                rotX = 0; rotY = 0; zoom = 0.92; panX = 20; panY = 20;
            } else if (mode === 'deep') {
                rotX = 36; rotY = -26; zoom = 1.05; panX = 50; panY = -40;
            }
            baseRotX = rotX;
            baseRotY = rotY;
            applyCameraTransform();
            drawStaticCables();
        }

        function toggleCinematicCamera() {
            isCinematic = !isCinematic;
            updateCinematicButtonUI();
        }

        function updateCinematicButtonUI() {
            const btn = document.getElementById("btn-cinematic");
            if (isCinematic) {
                btn.classList.add("active-glow");
                btn.innerText = "🎥 Cinematic Orbit: ON";
            } else {
                btn.classList.remove("active-glow");
                btn.innerText = "🎥 Cinematic Orbit: OFF";
            }
        }

        function toggleMoneyStream() {
            isMoneyStreamRunning = !isMoneyStreamRunning;
            const btn = document.getElementById("btn-toggle-money");
            if (isMoneyStreamRunning) {
                btn.classList.add("money-active");
                btn.innerText = "💸 Money Stream: ON";
            } else {
                btn.classList.remove("money-active");
                btn.innerText = "⏸ Money Stream: PAUSED";
            }
        }

        function replayVictimBurst() {
            globalMoneyTime = 0;
            jumpToStep(1);
            const vc = document.getElementById("card-victim");
            vc.classList.remove("victim-pulsing");
            void vc.offsetWidth; // reflow
            vc.classList.add("victim-pulsing");
        }

        function setStreamSpeed(speed) {
            streamSpeed = speed;
            document.querySelectorAll("#sidebar-left .btn-step").forEach(b => b.classList.remove("active-glow"));
            const lbl = document.getElementById("speed-label");
            if (speed === 0.5) {
                lbl.innerText = "0.5x Slow (Detailed View)";
            } else if (speed === 1.0) {
                document.getElementById("speed-normal").classList.add("active-glow");
                lbl.innerText = "1.0x Normal";
            } else if (speed === 2.0) {
                lbl.innerText = "2.0x Fast (Rapid Flow)";
            }
        }

        // 1-Click Dual Layout Switcher Function
        function switchLayoutMode(mode) {
            currentLayout = mode;
            const btnCirc = document.getElementById("btn-layout-circular");
            const btnCols = document.getElementById("btn-layout-columns");
            const hudMode = document.getElementById("motion-mode-text");
            const baseplates = document.querySelectorAll(".baseplate");

            if (mode === 'circular') {
                btnCirc.classList.add("active");
                btnCols.classList.remove("active");
                hudMode.innerText = "⭕ Circular Orbit Active";
                orbitalRings.style.opacity = "1";
                baseplates.forEach(bp => bp.style.opacity = "0");
                rotX = 14; rotY = -8; baseRotX = 14; baseRotY = -8;
            } else {
                btnCols.classList.add("active");
                btnCirc.classList.remove("active");
                hudMode.innerText = "📐 3D Columns Active";
                orbitalRings.style.opacity = "0";
                baseplates.forEach(bp => bp.style.opacity = "1");
                rotX = 20; rotY = -12; baseRotX = 20; baseRotY = -12;
            }

            applyCameraTransform();

            // Apply target positions
            const coords = LAYOUT_COORDINATES[mode];
            for (const [id, pos] of Object.entries(coords)) {
                const el = document.getElementById(id);
                if (el) {
                    el.style.left = pos.left + "px";
                    el.style.top = pos.top + "px";
                }
            }

            // Redraw cables during transition
            let animFrames = 0;
            function transitionRedraw() {
                drawStaticCables();
                animFrames++;
                if (animFrames < 45) {
                    requestAnimationFrame(transitionRedraw);
                }
            }
            requestAnimationFrame(transitionRedraw);
        }

        // Viewport Drag & Orbit Listeners
        viewport.addEventListener("mousedown", (e) => {
            if (e.target.closest(".forensic-card") || e.target.closest("button")) return;
            isDragging = true;
            userInteracting = true;
            clearTimeout(idleTimer);
            lastX = e.clientX;
            lastY = e.clientY;
        });

        window.addEventListener("mousemove", (e) => {
            if (!isDragging) return;
            const dx = e.clientX - lastX;
            const dy = e.clientY - lastY;
            lastX = e.clientX;
            lastY = e.clientY;

            if (e.shiftKey) {
                panX += dx;
                panY += dy;
            } else {
                rotY += dx * 0.35;
                rotX -= dy * 0.35;
                rotX = Math.max(-10, Math.min(65, rotX));
                baseRotY = rotY;
                baseRotX = rotX;
            }
            applyCameraTransform();
        });

        window.addEventListener("mouseup", () => {
            isDragging = false;
            idleTimer = setTimeout(() => { userInteracting = false; }, 3500);
        });

        viewport.addEventListener("wheel", (e) => {
            e.preventDefault();
            zoom -= e.deltaY * 0.0012;
            zoom = Math.max(0.5, Math.min(1.8, zoom));
            applyCameraTransform();
        });

        // Compute smooth curved cable control points
        function getCableCurvePoints(fEl, tEl) {
            const fRect = { left: fEl.offsetLeft, top: fEl.offsetTop, w: fEl.offsetWidth, h: fEl.offsetHeight };
            const tRect = { left: tEl.offsetLeft, top: tEl.offsetTop, w: tEl.offsetWidth, h: tEl.offsetHeight };

            const fCenter = { x: fRect.left + fRect.w / 2, y: fRect.top + fRect.h / 2 };
            const tCenter = { x: tRect.left + tRect.w / 2, y: tRect.top + tRect.h / 2 };

            if (currentLayout === 'columns') {
                const p0 = { x: fRect.left + fRect.w, y: fCenter.y };
                const p3 = { x: tRect.left, y: tCenter.y };
                const dx = p3.x - p0.x;
                const p1 = { x: p0.x + dx * 0.45, y: p0.y };
                const p2 = { x: p0.x + dx * 0.55, y: p3.y };
                return { p0, p1, p2, p3 };
            } else {
                // Circular Orbit Layout: determine closest edge anchors
                const angle = Math.atan2(tCenter.y - fCenter.y, tCenter.x - fCenter.x);
                const p0 = {
                    x: fCenter.x + Math.cos(angle) * (fRect.w / 2),
                    y: fCenter.y + Math.sin(angle) * (fRect.h / 2)
                };
                const p3 = {
                    x: tCenter.x - Math.cos(angle) * (tRect.w / 2),
                    y: tCenter.y - Math.sin(angle) * (tRect.h / 2)
                };

                // Curve bow perpendicular or radial
                const midX = (p0.x + p3.x) / 2;
                const midY = (p0.y + p3.y) / 2;
                const dist = Math.hypot(p3.x - p0.x, p3.y - p0.y);
                const normX = -(p3.y - p0.y) / dist;
                const normY = (p3.x - p0.x) / dist;

                // Subtle outward arc from center (800, 460)
                const toCenter = (midX - 800) * normX + (midY - 460) * normY;
                const sign = toCenter >= 0 ? 1 : -1;
                const bow = Math.min(60, dist * 0.18) * sign;

                const p1 = { x: p0.x * 0.65 + midX * 0.35 + normX * bow, y: p0.y * 0.65 + midY * 0.35 + normY * bow };
                const p2 = { x: p3.x * 0.65 + midX * 0.35 + normX * bow, y: p3.y * 0.65 + midY * 0.35 + normY * bow };

                return { p0, p1, p2, p3 };
            }
        }

        // Cubic Bezier Point Calculation
        function getCubicBezierPoint(p0, p1, p2, p3, t) {
            const u = 1 - t;
            const tt = t * t;
            const uu = u * u;
            const uuu = uu * u;
            const ttt = tt * t;

            const x = uuu * p0.x + 3 * uu * t * p1.x + 3 * u * tt * p2.x + ttt * p3.x;
            const y = uuu * p0.y + 3 * uu * t * p1.y + 3 * u * tt * p2.y + ttt * p3.y;
            return { x, y };
        }

        // Draw Rounded Rectangle Helper on Canvas
        function drawRoundedPill(ctx, x, y, width, height, radius, fillStyle, strokeStyle, shadowColor) {
            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();

            ctx.shadowColor = shadowColor || strokeStyle;
            ctx.shadowBlur = 14;
            ctx.fillStyle = fillStyle;
            ctx.fill();

            ctx.lineWidth = 2;
            ctx.strokeStyle = strokeStyle;
            ctx.stroke();
            ctx.restore();
        }

        // Real-Time 60 FPS Render Loop with Moving Money Badges & Orbital Sparkles
        function renderMovingMoneyLoop(timestamp) {
            frameCount++;
            if (timestamp - lastFpsUpdate >= 1000) {
                const fps = Math.round((frameCount * 1000) / (timestamp - lastFpsUpdate));
                document.getElementById("fps-counter").innerText = fps;
                frameCount = 0;
                lastFpsUpdate = timestamp;
            }

            const dt = (timestamp - lastTimestamp) / 1000;
            lastTimestamp = timestamp;

            // 1. Cinematic Camera Glide Animation
            if (isCinematic && !isDragging && !userInteracting) {
                rotY += 0.04 * streamSpeed;
                rotX = baseRotX + Math.sin(timestamp * 0.0006) * 3;
                panY = -10 + Math.cos(timestamp * 0.0005) * 4;
                applyCameraTransform();
            }

            // 2. Clear Motion Canvas
            mCtx.clearRect(0, 0, motionCanvas.width, motionCanvas.height);

            // 3. Increment Money Stream Time
            if (isMoneyStreamRunning) {
                globalMoneyTime += dt * streamSpeed;
            }

            // 4. In Circular Mode, draw extra orbiting money sparkles along the orbital rings
            if (currentLayout === 'circular' && isMoneyStreamRunning) {
                const orbits = [
                    { rx: 270, ry: 190, color: "#00f0ff", count: 4, speed: 0.18, label: "₹" },
                    { rx: 475, ry: 290, color: "#f59e0b", count: 5, speed: -0.12, label: "₹" },
                    { rx: 660, ry: 385, color: "#a855f7", count: 6, speed: 0.08, label: "₹" }
                ];

                orbits.forEach(orb => {
                    for (let i = 0; i < orb.count; i++) {
                        const angle = globalMoneyTime * orb.speed + (i * Math.PI * 2 / orb.count);
                        const ox = 800 + orb.rx * Math.cos(angle);
                        const oy = 460 + orb.ry * Math.sin(angle);

                        mCtx.save();
                        mCtx.beginPath();
                        mCtx.arc(ox, oy, 4, 0, Math.PI * 2);
                        mCtx.fillStyle = orb.color;
                        mCtx.shadowColor = orb.color;
                        mCtx.shadowBlur = 10;
                        mCtx.fill();

                        // Tiny currency sign
                        mCtx.font = "bold 9px monospace";
                        mCtx.fillStyle = "#ffffff";
                        mCtx.textAlign = "center";
                        mCtx.textBaseline = "middle";
                        mCtx.fillText("₹", ox, oy - 8);
                        mCtx.restore();
                    }
                });
            }

            let activeStreamsCount = 0;

            // 5. Render Moving Money Badges & Trailing Sparkles
            CABLE_LINKS.forEach((link) => {
                const fEl = document.getElementById(link.from);
                const tEl = document.getElementById(link.to);
                if (!fEl || !tEl) return;

                const isActive = (activeStep === 5) || (link.step <= activeStep);
                if (!isActive) return;

                activeStreamsCount++;

                const { p0, p1, p2, p3 } = getCableCurvePoints(fEl, tEl);
                const numPackets = link.density || 2;
                const baseSpeed = link.speed || 0.22;

                for (let i = 0; i < numPackets; i++) {
                    const offset = i / numPackets;
                    const progress = (globalMoneyTime * baseSpeed + offset) % 1.0;

                    // Moving Money Position
                    const pt = getCubicBezierPoint(p0, p1, p2, p3, progress);

                    // Trailing Comet of Coins/Sparkles
                    for (let s = 4; s >= 1; s--) {
                        const trailT = Math.max(0, progress - s * 0.025);
                        const trailPt = getCubicBezierPoint(p0, p1, p2, p3, trailT);

                        mCtx.save();
                        mCtx.beginPath();
                        mCtx.arc(trailPt.x, trailPt.y, 4 - s * 0.6, 0, Math.PI * 2);
                        mCtx.fillStyle = link.color;
                        mCtx.globalAlpha = (0.5 / s);
                        mCtx.shadowColor = link.color;
                        mCtx.shadowBlur = 8;
                        mCtx.fill();
                        mCtx.restore();
                    }

                    // Draw the Prominent Moving Money Pill Capsule
                    const pillWidth = 86;
                    const pillHeight = 24;
                    const pillX = pt.x - pillWidth / 2;
                    const pillY = pt.y - pillHeight / 2;

                    // Slight floating scale pulse
                    const scalePulse = 1.0 + Math.sin(globalMoneyTime * 8 + i) * 0.05;

                    mCtx.save();
                    mCtx.translate(pt.x, pt.y);
                    mCtx.scale(scalePulse, scalePulse);
                    mCtx.translate(-pt.x, -pt.y);

                    // Pill Background & Glowing Border
                    drawRoundedPill(mCtx, pillX, pillY, pillWidth, pillHeight, 12, "rgba(8, 14, 28, 0.94)", link.color, link.color);

                    // Inner Money Text (Exact Rupees Traveling)
                    mCtx.font = "bold 11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
                    mCtx.fillStyle = "#ffffff";
                    mCtx.textAlign = "center";
                    mCtx.textBaseline = "middle";
                    mCtx.shadowColor = link.color;
                    mCtx.shadowBlur = 4;
                    mCtx.fillText(link.moneyText, pt.x, pt.y + 1);

                    mCtx.restore();

                    // Generate impact explosion when money hits destination
                    if (progress > 0.96 && progress < 0.99 && Math.random() < 0.3) {
                        shockwaves.push({
                            x: p3.x,
                            y: p3.y,
                            color: link.color,
                            radius: 8,
                            maxRadius: 36,
                            alpha: 1.0
                        });
                    }
                }
            });

            document.getElementById("active-streams-count").innerText = `${activeStreamsCount} Active Streams`;

            // 6. Render Expanding Impact Shockwaves
            for (let i = shockwaves.length - 1; i >= 0; i--) {
                const sw = shockwaves[i];
                sw.radius += dt * 50;
                sw.alpha -= dt * 1.8;

                if (sw.alpha <= 0 || sw.radius >= sw.maxRadius) {
                    shockwaves.splice(i, 1);
                    continue;
                }

                mCtx.save();
                mCtx.beginPath();
                mCtx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
                mCtx.strokeStyle = sw.color;
                mCtx.lineWidth = 2.5;
                mCtx.globalAlpha = Math.max(0, sw.alpha);
                mCtx.shadowColor = sw.color;
                mCtx.shadowBlur = 12;
                mCtx.stroke();
                mCtx.restore();
            }

            requestAnimationFrame(renderMovingMoneyLoop);
        }

        // Draw Static SVG Cable Backbones
        function drawStaticCables() {
            cablesCanvas.innerHTML = "";

            CABLE_LINKS.forEach(link => {
                const fEl = document.getElementById(link.from);
                const tEl = document.getElementById(link.to);
                if (!fEl || !tEl) return;

                const isActive = (activeStep === 5) || (link.step <= activeStep);
                const opacity = isActive ? (link.step === activeStep || activeStep === 5 ? 1 : 0.4) : 0.08;

                const { p0, p1, p2, p3 } = getCableCurvePoints(fEl, tEl);
                const pathString = `M ${p0.x} ${p0.y} C ${p1.x} ${p1.y}, ${p2.x} ${p2.y}, ${p3.x} ${p3.y}`;

                // Background Depth Shadow
                const pBg = document.createElementNS("http://www.w3.org/2000/svg", "path");
                pBg.setAttribute("d", pathString);
                pBg.setAttribute("class", "cable-shadow");
                pBg.style.opacity = opacity;
                cablesCanvas.appendChild(pBg);

                // Foreground Glowing Cable
                const pFg = document.createElementNS("http://www.w3.org/2000/svg", "path");
                pFg.setAttribute("d", pathString);
                pFg.setAttribute("class", isActive ? "cable-glow cable-dash" : "cable-glow");
                pFg.setAttribute("stroke", link.color);
                pFg.style.opacity = opacity;
                cablesCanvas.appendChild(pFg);
            });
        }

        // Step Navigation System
        function jumpToStep(step) {
            activeStep = step;
            renderStepState();
        }

        function stepNext() {
            if (activeStep < 5) jumpToStep(activeStep + 1);
            else jumpToStep(1);
        }

        function stepPrevious() {
            if (activeStep > 1) jumpToStep(activeStep - 1);
        }

        function toggleAutoPlay() {
            const btn = document.getElementById("btn-play-pause");
            if (isAutoPlay) {
                clearInterval(autoPlayTimer);
                isAutoPlay = false;
                btn.innerText = "⏵ Auto Play";
                btn.classList.remove("active");
            } else {
                isAutoPlay = true;
                btn.innerText = "⏸ Pause Play";
                btn.classList.add("active");
                autoPlayTimer = setInterval(stepNext, 4500);
            }
        }

        function showCompleteTrail() {
            jumpToStep(5);
        }

        function renderStepState() {
            for (let i = 1; i <= 5; i++) {
                const b = document.getElementById(`step-btn-${i}`);
                if (b) {
                    if (i === activeStep) b.classList.add("current");
                    else b.classList.remove("current");
                }
            }

            const story = STEP_STORIES[activeStep];
            document.getElementById("step-badge-text").innerText = story.badge;
            document.getElementById("narrative-english").innerText = (activeLang === 'hi') ? story.hi : story.en;
            document.getElementById("narrative-hindi").innerText = (activeLang === 'hi') ? story.en : story.hi;

            const cards = document.querySelectorAll(".forensic-card");
            cards.forEach(c => c.classList.remove("spotlight", "dimmed"));

            if (activeStep === 1) {
                spotlightCards(["card-victim", "card-iob", "card-idfc", "card-icici"]);
            } else if (activeStep === 2) {
                spotlightCards(["card-idfc", "card-iob", "card-iob-hold"]);
            } else if (activeStep === 3) {
                spotlightCards(["card-icici", "card-payu", "card-iob", "card-sbi"]);
            } else if (activeStep === 4) {
                spotlightCards(["card-iob-atm", "card-sbi-atm", "card-citi", "card-payu", "card-sbi", "card-iob"]);
            } else if (activeStep === 5) {
                cards.forEach(c => c.classList.add("spotlight"));
            }

            drawStaticCables();
        }

        function spotlightCards(activeIds) {
            const cards = document.querySelectorAll(".forensic-card");
            cards.forEach(c => {
                if (activeIds.includes(c.id)) c.classList.add("spotlight");
                else c.classList.add("dimmed");
            });
        }

        // Search Filter
        function handleSearch(query) {
            const q = query.trim().toLowerCase();
            const cards = document.querySelectorAll(".forensic-card");
            if (!q) {
                renderStepState();
                return;
            }

            cards.forEach(c => {
                const text = c.innerText.toLowerCase();
                if (text.includes(q)) {
                    c.classList.remove("dimmed");
                    c.classList.add("spotlight");
                } else {
                    c.classList.remove("spotlight");
                    c.classList.add("dimmed");
                }
            });
        }

        // Inspector Drawer Functions
        function openInspector(key) {
            const data = ENTITY_REGISTRY[key];
            if (!data) return;

            document.getElementById("ins-icon").innerText = data.icon;
            document.getElementById("ins-title").innerText = data.title;
            document.getElementById("ins-name").innerText = data.name;
            document.getElementById("ins-bank").innerText = data.bank;
            document.getElementById("ins-acc").innerText = data.acc;
            document.getElementById("ins-utr").innerText = data.utr;
            document.getElementById("ins-layer").innerText = data.layer;
            document.getElementById("ins-amt").innerText = data.amt;
            document.getElementById("ins-amt").style.color = data.color;
            document.getElementById("ins-action").innerText = data.action;

            document.getElementById("inspector-drawer").classList.add("open");
        }

        function closeInspector() {
            document.getElementById("inspector-drawer").classList.remove("open");
        }

        function copyAccountNo() {
            const acc = document.getElementById("ins-acc").innerText;
            navigator.clipboard.writeText(acc).then(() => {
                alert("Account Number copied to clipboard: " + acc);
            });
        }

        // Toggle Left Sidebar
        function toggleSidebar() {
            document.getElementById("sidebar-left").classList.toggle("collapsed");
        }

        // Language Switcher
        function toggleLanguage() {
            activeLang = (activeLang === 'en') ? 'hi' : 'en';
            document.getElementById("lang-indicator").innerText = (activeLang === 'en') ? "🌐 EN / हिन्दी" : "🌐 हिन्दी / EN";
            const story = STEP_STORIES[activeStep];
            if (activeLang === 'hi') {
                document.getElementById("narrative-english").innerText = story.hi;
                document.getElementById("narrative-hindi").innerText = story.en;
            } else {
                document.getElementById("narrative-english").innerText = story.en;
                document.getElementById("narrative-hindi").innerText = story.hi;
            }
        }

        // Populate Left Sidebar Roster
        function initRoster() {
            const container = document.getElementById("roster-container");
            container.innerHTML = "";
            for (const [key, item] of Object.entries(ENTITY_REGISTRY)) {
                const div = document.createElement("div");
                div.className = "roster-item";
                div.onclick = () => {
                    openInspector(key);
                    const el = document.getElementById(item.id);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.classList.add("spotlight");
                    }
                };

                div.innerHTML = `
                    <div class="roster-info">
                        <span class="roster-name">${item.icon} ${item.title}</span>
                        <span class="roster-sub">${item.acc}</span>
                    </div>
                    <span class="roster-badge" style="background: rgba(255,255,255,0.06); color: ${item.color}; border: 1px solid ${item.color};">
                        ${item.amt.split(' ')[0]}
                    </span>
                `;
                container.appendChild(div);
            }
        }

        // Boot Init & Render Engine Start
        window.addEventListener("load", () => {
            initRoster();
            switchLayoutMode('circular'); // Default to circular mode
            jumpToStep(1);
            requestAnimationFrame(renderMovingMoneyLoop);
        });
    </script>
</body>
</html>
'''

def main():
    print("Writing Circular Orbital Money Trail 3D Visualizer...")
    for path in OUTPUT_PATHS:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(HTML_CONTENT)
        print(f"  [OK] Saved: {path} ({len(HTML_CONTENT)} bytes)")

if __name__ == "__main__":
    main()
