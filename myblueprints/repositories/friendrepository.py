# --- REPOSITORY KLASS ---
#myblueprints/repositories/friendrepository.py
# Denna klass sköter all kontakt med JSON-filen
import json
import os
class FriendRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def _load(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _save(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_all(self):
        data = self._load()
        # Vi sorterar listan 'data' baserat på nyckeln 'id' i varje dictionary.
        # sorted() returnerar en ny, sorterad lista.
        sorted_data = sorted(data, key=lambda friend: friend['id'])
        return sorted_data #self._load()

    def get_by_id(self, friend_id):
        data = self._load()
        return next((f for f in data if f['id'] == friend_id), None)

    def add(self, friend_dict):
        data = self._load()
        data.append(friend_dict)
        self._save(data)
        return friend_dict

    def update(self, friend_id, updates):
        data = self._load()
        for friend in data:
            if friend['id'] == friend_id:
                friend.update(updates)
                self._save(data)
                return friend
        return None

    def delete(self, friend_id):
        data = self._load()
        if not any(f['id'] == friend_id for f in data):
            return False
        updated_data = [f for f in data if f['id'] != friend_id]
        self._save(updated_data)
        return True
