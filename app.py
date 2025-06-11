from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii
from flask import Flask, request, jsonify
import requests
import time
from data_pb2 import response
from secret import key, iv

app = Flask(__name__)

def create_complete_response(user_id):
    """Create a complete response protobuf with ALL fields from data.proto"""
    resp = response()
    
    # Basic fields (1-9)
    resp.id = user_id
    resp.special_code = f"SPECIAL_{user_id % 1000}"
    resp.timestamp1 = int(time.time())
    resp.value_a = 100 + (user_id % 50)
    resp.status_code = 200 if user_id % 3 else 400
    resp.sub_type = user_id % 5
    resp.version = 1
    resp.level = 10 + (user_id % 90)
    resp.flags = 0x1 | 0x4 if user_id % 2 else 0x2
    
    # String fields (12-15)
    resp.welcome_message = f"Welcome, Player {user_id}!"
    resp.region = "IND" if user_id % 2 else "NA"
    resp.json_metadata = '{"premium": true}' if user_id % 3 else '{"premium": false}'
    resp.big_numbers = "1000000,2000000,3000000"
    
    # Numeric fields (20, 22, 33, 35-40)
    resp.balance = 5000 + (user_id % 5000)
    resp.score = 10000 + (user_id % 10000)
    resp.upgrades = 5 + (user_id % 10)
    resp.achievements = 3 + (user_id % 7)
    resp.total_playtime = 3600 + (user_id % 86400)
    resp.energy = 100 if user_id % 3 else 50
    resp.rank = 1 + (user_id % 100)
    resp.xp = 1000 + (user_id % 9000)
    resp.timestamp2 = int(time.time()) - (3600 * 24)
    resp.error_code = 0 if user_id % 3 else 404
    
    # Last active (44)
    resp.last_active = int(time.time()) - (3600 * (user_id % 24))
    
    # Guild details (47)
    resp.guild_details.region = resp.region
    resp.guild_details.clan_id = 1000 + user_id
    resp.guild_details.members_online = 5 + (user_id % 15)
    resp.guild_details.total_members = 20 + (user_id % 30)
    resp.guild_details.regional = 1 if user_id % 2 else 0
    resp.guild_details.reward_time = int(time.time()) + 86400
    resp.guild_details.expire_time = int(time.time()) + 2592000
    
    # Empty field (49)
    resp.empty_field = ""
    
    return resp

def protobuf_to_dict(pb_message):
    """Convert response protobuf to dictionary with ALL fields"""
    return {
        # Basic fields (1-9)
        "id": pb_message.id,
        "special_code": pb_message.special_code,
        "timestamp1": pb_message.timestamp1,
        "value_a": pb_message.value_a,
        "status_code": pb_message.status_code,
        "sub_type": pb_message.sub_type,
        "version": pb_message.version,
        "level": pb_message.level,
        "flags": pb_message.flags,
        
        # String fields (12-15)
        "welcome_message": pb_message.welcome_message,
        "region": pb_message.region,
        "json_metadata": pb_message.json_metadata,
        "big_numbers": pb_message.big_numbers,
        
        # Numeric fields (20, 22, 33, 35-40)
        "balance": pb_message.balance,
        "score": pb_message.score,
        "upgrades": pb_message.upgrades,
        "achievements": pb_message.achievements,
        "total_playtime": pb_message.total_playtime,
        "energy": pb_message.energy,
        "rank": pb_message.rank,
        "xp": pb_message.xp,
        "timestamp2": pb_message.timestamp2,
        "error_code": pb_message.error_code,
        
        # Last active (44)
        "last_active": pb_message.last_active,
        
        # Guild details (47)
        "guild_details": {
            "region": pb_message.guild_details.region,
            "clan_id": pb_message.guild_details.clan_id,
            "members_online": pb_message.guild_details.members_online,
            "total_members": pb_message.guild_details.total_members,
            "regional": pb_message.guild_details.regional,
            "reward_time": pb_message.guild_details.reward_time,
            "expire_time": pb_message.guild_details.expire_time
        },
        
        # Empty field (49)
        "empty_field": pb_message.empty_field,
        
        # Metadata
        "proto_fields_included": "All fields from data.proto (1-49)",
        "timestamp": int(time.time())
    }

@app.route('/player-data', methods=['GET'])
def player_data():
    """Endpoint returning ALL fields from data.proto"""
    uid = request.args.get('uid')
    region = request.args.get('region')

    if not uid or not region:
        return jsonify({"error": "Missing 'uid' or 'region' parameter"}), 400

    try:
        user_id = int(uid)
    except ValueError:
        return jsonify({"error": "Invalid UID format"}), 400

    # Create complete response with all fields
    pb_response = create_complete_response(user_id)
    
    # Convert to dictionary for JSON response
    response_data = protobuf_to_dict(pb_response)
    response_data['request_region'] = region.upper()
    response_data['credit'] = "@Ujjaiwal"

    return jsonify(response_data)

@app.route('/encrypted-data', methods=['GET'])
def encrypted_data():
    """Endpoint returning encrypted protobuf data"""
    uid = request.args.get('uid')
    
    if not uid:
        return jsonify({"error": "Missing 'uid' parameter"}), 400

    try:
        user_id = int(uid)
    except ValueError:
        return jsonify({"error": "Invalid UID format"}), 400

    # Create protobuf
    pb_response = create_complete_response(user_id)
    serialized = pb_response.SerializeToString()
    
    # Encrypt the data
    key_bytes = key.encode()[:16]
    iv_bytes = iv.encode()[:16]
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    padded_data = pad(serialized, AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    
    return jsonify({
        "encrypted_data": binascii.hexlify(encrypted_data).decode(),
        "encryption_info": {
            "algorithm": "AES-CBC",
            "key_size": 128,
            "padding": "PKCS7"
        },
        "timestamp": int(time.time())
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)