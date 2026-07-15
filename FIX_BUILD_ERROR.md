# Fix: "linker `cc` not found" Error

## The Problem
The Python package `pydantic-core` needs a C compiler to build, but GCC is not installed on your system.

## The Solution

Run this single command to install the C compiler and development tools:

```bash
sudo dnf install -y gcc gcc-c++ python3-devel
```

This installs:
- `gcc` - C compiler (the missing 'cc')
- `gcc-c++` - C++ compiler
- `python3-devel` - Python development headers

**It will take about 1-2 minutes to install (~150MB).**

## After Installation

Once the install completes, run:

```bash
cd /home/ybounkib/intern_project/TeamAgent/web
./start.sh
```

## Verification

To verify GCC is installed:
```bash
gcc --version
```

You should see something like:
```
gcc (GCC) 14.x.x
```

---

## Alternative: Use Pre-built Wheels

If you can't install GCC for some reason, you can try using older versions of the packages that have pre-built wheels:

Edit `web/backend/requirements.txt` and change:
```
fastapi==0.115.0
pydantic==2.9.2
```

To:
```
fastapi==0.104.1
pydantic==2.5.0
```

Then run `./start.sh` again.

But **installing GCC is the better solution** as it will work for all packages.

---

## Quick Commands Summary

```bash
# 1. Install GCC
sudo dnf install -y gcc gcc-c++ python3-devel

# 2. Start the application
cd /home/ybounkib/intern_project/TeamAgent/web
./start.sh
```

That's it!
