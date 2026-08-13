import asyncio
import httpx

async def test():
    async with httpx.AsyncClient() as client:
        # Test 1: Fetch formats
        res = await client.post("http://127.0.0.1:8000/api/info", json={"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"})
        print("Info fetch status:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            print("Title:", data.get("title"))
            formats = data.get("formats", [])
            print("Formats found:", len(formats))
            
            if formats:
                format_id = formats[0]["id"]
                # Test 2: Process video
                res2 = await client.post("http://127.0.0.1:8000/api/process", json={"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw", "format_id": format_id})
                print("Process status:", res2.status_code)
                if res2.status_code == 200:
                    task_id = res2.json().get("task_id")
                    print("Task ID:", task_id)
                    
                    # Test 3: Poll status
                    for _ in range(10):
                        await asyncio.sleep(2)
                        res3 = await client.get(f"http://127.0.0.1:8000/api/status/{task_id}")
                        status = res3.json().get("status")
                        print("Current status:", status)
                        if status == "completed":
                            print("Download complete!")
                            break
                        elif status == "failed":
                            print("Download failed!", res3.json().get("error"))
                            break

asyncio.run(test())
