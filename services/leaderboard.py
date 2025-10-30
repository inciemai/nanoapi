from flask import Blueprint, jsonify, request
from config import db, ADMIN_USERNAME
from utils.auth import admin_required
import math

leaderboard_bp = Blueprint('leaderboard', __name__)


@leaderboard_bp.route('/leaderboard', methods=['GET'])
@admin_required
def get_leaderboard():
    try:
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500

        # Pagination: support named (page, limit) and positional (/leaderboard?2&10)
        page = request.args.get('page', default=None, type=int)
        per_page = request.args.get('limit', default=None, type=int)

        if page is None or per_page is None:
            if ('page' not in request.args) and ('limit' not in request.args) and len(request.args) > 0:
                numeric_keys = []
                for k in request.args.keys():
                    if isinstance(k, str) and k.isdigit():
                        numeric_keys.append(int(k))
                if len(numeric_keys) >= 1 and page is None:
                    page = numeric_keys[0]
                if len(numeric_keys) >= 2 and per_page is None:
                    per_page = numeric_keys[1]

        if page is None:
            page = 1
        if per_page is None:
            per_page = 10
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 100:
            per_page = 100

        # Aggregate quiz results per user
        pipeline = [
            {
                '$group': {
                    '_id': '$user_id',
                    'total_quizzes_attempted': {'$sum': 1},
                    'total_correct': {'$sum': '$correct_answers'},
                    'total_questions': {'$sum': '$total_questions'},
                    'total_time_taken': {'$sum': '$time_taken'},
                    'average_score': {'$avg': {'$divide': ['$correct_answers', '$total_questions']}}
                }
            },
            {
                '$project': {
                    'user_id': '$_id',
                    'total_quizzes_attempted': 1,
                    'total_correct': 1,
                    'total_questions': 1,
                    'total_time_taken': 1,
                    'average_score': {'$multiply': ['$average_score', 100]}
                }
            }
        ]

        aggregated_results = list(db.quiz_results.aggregate(pipeline))

        # Load all users
        all_users_dict = {}
        for user in db.users.find():
            all_users_dict[str(user['_id'])] = user

        # Build full leaderboard entries (include users with no attempts)
        leaderboard_entries = []
        processed_user_ids = set()

        for result in aggregated_results:
            uid = str(result['user_id'])
            processed_user_ids.add(uid)
            if uid in all_users_dict:
                user = all_users_dict[uid]
                leaderboard_entries.append({
                    'user_id': uid,
                    'name': user.get('name', 'Unknown'),
                    'attempted_questions': result.get('total_questions', 0),
                    'time_taken': round(result.get('total_time_taken', 0), 2),
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'total_correct': result.get('total_correct', 0),
                    'total_questions': result.get('total_questions', 0),
                    'average_score': round(result.get('average_score', 0.0), 2)
                })
            else:
                is_admin = uid.lower() == 'admin'
                leaderboard_entries.append({
                    'user_id': uid,
                    'name': 'Admin' if is_admin else 'Unknown User',
                    'attempted_questions': result.get('total_questions', 0),
                    'time_taken': round(result.get('total_time_taken', 0), 2),
                    'email': ADMIN_USERNAME if is_admin else '',
                    'phone': '',
                    'total_correct': result.get('total_correct', 0),
                    'total_questions': result.get('total_questions', 0),
                    'average_score': round(result.get('average_score', 0.0), 2)
                })

        for uid, user in all_users_dict.items():
            if uid not in processed_user_ids:
                leaderboard_entries.append({
                    'user_id': uid,
                    'name': user.get('name', 'Unknown'),
                    'attempted_questions': 0,
                    'time_taken': 0.0,
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'total_correct': 0,
                    'total_questions': 0,
                    'average_score': 0.0
                })

        # Sort: higher average score first, then lower time_taken
        leaderboard_entries.sort(key=lambda x: (-x['average_score'], x['time_taken']))

        # Assign rank and drop average_score from response
        for index, entry in enumerate(leaderboard_entries, start=1):
            entry['rank'] = index
            entry.pop('average_score', None)

        # Pagination over full list
        total_items = len(leaderboard_entries)
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        paginated = leaderboard_entries[start:end]

        return jsonify({
            'status': True,
            'leaderboard_preview': paginated,
            'pagination': {
                'total_items': total_items,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': per_page,
                'has_next_page': page < total_pages,
                'has_prev_page': page > 1
            }
        }), 200
    except Exception as e:
        return jsonify({'status': False, 'error': str(e)}), 500


