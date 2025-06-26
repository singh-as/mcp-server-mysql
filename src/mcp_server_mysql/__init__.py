from . import server
import asyncio

def main():
   asyncio.run(server.run_stdio())

# Expose important items at package level
__all__ = ['main', 'server']
