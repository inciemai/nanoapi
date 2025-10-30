from flask import Blueprint, request, jsonify
from config import db
from utils.auth import admin_required
import math

get_users_bp = Blueprint('get_users', __name__)

@get_users_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        print("[Get Users] Fetching users with pagination...")
        if db is None:
            print("[Get Users] ERROR: Database connection failed")
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Pagination parameters (support both named and positional query params)
        page = request.args.get('page', default=None, type=int)
        per_page = request.args.get('limit', default=None, type=int)

        # Fallback: handle positional style like /users?2&10 (non-standard but requested)
        if page is None or per_page is None:
            # If named params missing, try to infer from unnamed keys
            if ('page' not in request.args) and ('limit' not in request.args) and len(request.args) > 0:
                numeric_keys = []
                for k in request.args.keys():
                    # keys may be like '2' or '10' with empty values
                    if isinstance(k, str) and k.isdigit():
                        numeric_keys.append(int(k))
                if len(numeric_keys) >= 1 and page is None:
                    page = numeric_keys[0]
                if len(numeric_keys) >= 2 and per_page is None:
                    per_page = numeric_keys[1]

        # Defaults if still None
        if page is None:
            page = 1
        if per_page is None:
            per_page = 10
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:  # Limit max items per page
            per_page = 100
        
        # Get total count
        total_users = db.users.count_documents({})
        print(f"[Get Users] Total users: {total_users}")
        
        # Calculate pagination
        total_pages = math.ceil(total_users / per_page) if total_users > 0 else 1
        skip = (page - 1) * per_page
        
        print(f"[Get Users] Pagination: page={page}, per_page={per_page}, skip={skip}, total_pages={total_pages}")
        
        # Fetch users with pagination
        users = db.users.find({}, {'password': 0}).skip(skip).limit(per_page)
        user_list = []
        for user in users:
            user['_id'] = str(user['_id'])
            user_list.append(user)
        
        print(f"[Get Users] Returning {len(user_list)} users")
        
        return jsonify({
            'status': True,
            'users': user_list,
            'pagination': {
                'total_items': total_users,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': per_page,
                'has_next_page': page < total_pages,
                'has_prev_page': page > 1
            }
        }), 200
    except Exception as e:
        print(f"[Get Users] ERROR: {str(e)}")
        return jsonify({'status': False, 'error': str(e)}), 500

