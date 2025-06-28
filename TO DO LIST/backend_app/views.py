from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB connection
client = MongoClient("mongodb+srv://annapuranitkint:Whitedogblackdog@cluster1.fkkgbcr.mongodb.net/?retryWrites=true&w=majority")
db = client["todo_db"]
collection = db["tasks"]

class TaskListCreateView(APIView):
    def get(self, request):
        tasks = list(collection.find())
        for task in tasks:
            task["_id"] = str(task["_id"])
        return Response(tasks)

    def post(self, request):
        data = request.data
        title = data.get("title")
        completed = data.get("completed", False)

        if not title:
            return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)

        task = {"title": title, "completed": completed}
        result = collection.insert_one(task)
        return Response({"message": "Task added", "task_id": str(result.inserted_id)}, status=status.HTTP_201_CREATED)

class TaskUpdateDeleteView(APIView):
    def put(self, request, pk):
        data = request.data
        update = {
            "title": data.get("title"),
            "completed": data.get("completed", False)
        }
        result = collection.update_one({"_id": ObjectId(pk)}, {"$set": update})
        if result.matched_count == 0:
            return Response({"error": "Task not found"}, status=404)
        return Response({"message": "Task updated"})

    def delete(self, request, pk):
        result = collection.delete_one({"_id": ObjectId(pk)})
        if result.deleted_count == 0:
            return Response({"error": "Task not found"}, status=404)
        return Response({"message": "Task deleted"})
