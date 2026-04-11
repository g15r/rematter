# Changelog

All notable changes to this project will be documented in this file.

## 0.1.1 - 2026-04-11

### ✨ Features

#### Date-extract

* rename filename cmd to date-extract (#7) by @gwenwindflower in #7


#### Sync

* make type tag extraction optional in config (#5) by @gwenwindflower in #5


### 📼 Reverts

#### Testbox

* move Begin back to first step by @gwenwindflower


### 🚧 CI/CD

#### Testbox

* add blacksmith testbox (#4) by @gwenwindflower in #4

* move testbox Begin step after uv by @gwenwindflower in #6

* add bash step passing PATH to BASH_ENV (#8) by @gwenwindflower in #8


### 🛠️ Build System

#### Pypi

* move from brew to pypi release by @gwenwindflower


### 🧰 Tooling & Tasks

#### Release

* fix category ordering in git-cliff by @gwenwindflower


## 0.1.0 - 2026-04-09

### ✨ Features

#### General

* initial commit by @gwenwindflower


#### Config

* implement .rematter config + media syncing by @gwenwindflower


#### Sync

* build initial sync functionality by @gwenwindflower


#### Validate

* add validate cmd and solidify test patterns by @gwenwindflower

* sort keys based on schema ordering with fix flag by @gwenwindflower


### 🐛 Bug Fixes

#### Validate

* skip non-required properties by @gwenwindflower

* properly handle nulls and special files by @gwenwindflower


### 🧰 Tooling & Tasks

#### Amoxide

* add amoxide alias t for tests by @gwenwindflower


#### Markdown

* expand markdownlint rules by @gwenwindflower


#### Scripts

* add fix and cleanup scripts for mistakes by @gwenwindflower


### 🧪 Testing

#### Sync

* rm tests of removed mermaid support by @gwenwindflower


### 🤖 Coding Agents

#### Docs

* add initial context docs by @gwenwindflower


### 📚 Documentation

#### Readme

* add proper README and Apache 2.0 LICENSE by @gwenwindflower


#### Sync

* rm docs on removed mermaid support by @gwenwindflower


### 🛠️ Build System

#### Blacksmith

* upgrade runner to Blacksmith by @blacksmith-sh[bot]


#### Brew

* add pyinstaller build with homebrew release by @gwenwindflower


#### Gh

* update actions marketplace steps by @gwenwindflower

* update macos-13 runner to macos-15 by @gwenwindflower

* enable commit for homebrew-tap by @gwenwindflower


#### Git-cliff

* add git-cliff config by @gwenwindflower


### 🚧 CI/CD

#### GitHub Actions

* add initial GHA PR workflow by @gwenwindflower


