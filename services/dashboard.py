from flask import Blueprint, jsonify
from bson import ObjectId
from config import db, ADMIN_USERNAME
from utils.auth import admin_required

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """
    Dashboard endpoint that provides:
    - Total number of users
    - Number of users who attended the quiz
    - Leaderboard preview with all users' scores
    """
    try:
        print("[Dashboard] Attempting to fetch dashboard data...")
        
        # Check if database is connected
        if db is None:
            print("[Dashboard] ERROR: Database connection failed")
            return jsonify({
                'status': False,
                'error': 'Database connection failed'
            }), 500
        
        print("[Dashboard] Fetching total users count...")
        # Get total number of users
        total_users = db.users.count_documents({})
        print(f"[Dashboard] Total users: {total_users}")
        
        print("[Dashboard] Fetching users who attended quiz...")
        # Count distinct attendees EXCLUDING admin/system users
        distinct_user_ids = db.quiz_results.distinct('user_id')
        users_attended = len([uid for uid in distinct_user_ids if str(uid).lower() != 'admin'])
        print(f"[Dashboard] Users who attended quiz: {users_attended}")
        
        print("[Dashboard] Fetching leaderboard data...")
        # Get quiz results aggregated by user_id
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
        
        # Get aggregated quiz results
        aggregated_results = list(db.quiz_results.aggregate(pipeline))
        print(f"[Dashboard] Found {len(aggregated_results)} users with quiz results")
        
        # Get all users for matching user details
        print("[Dashboard] Fetching all users...")
        all_users_dict = {}
        for user in db.users.find():
            user_id_str = str(user['_id'])
            all_users_dict[user_id_str] = user
            print(f"[Dashboard] Loaded user: {user_id_str} ({user.get('name', 'Unknown')})")
        
        # Build leaderboard from quiz results
        leaderboard_preview = []
        processed_user_ids = set()
        
        for result in aggregated_results:
            user_id_key = str(result['user_id'])
            processed_user_ids.add(user_id_key)
            
            print(f"[Dashboard] Processing quiz result for user_id: {user_id_key}")
            
            # Try to find user details
            if user_id_key in all_users_dict:
                user = all_users_dict[user_id_key]
                leaderboard_preview.append({
                    'user_id': user_id_key,
                    'name': user.get('name', 'Unknown'),
                    'attempted_questions': result['total_questions'],
                    'time_taken': round(result.get('total_time_taken', 0), 2),
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'total_correct': result['total_correct'],
                    'total_questions': result['total_questions'],
                    'average_score': round(result['average_score'], 2)  # For sorting only
                })
                print(f"[Dashboard] Added user with quiz results: {user.get('name', 'Unknown')} - {result['total_correct']}/{result['total_questions']}")
            else:
                # User not found in users collection (e.g., admin user)
                # If admin, label clearly; otherwise, keep as Unknown User
                is_admin = user_id_key.lower() == 'admin'
                leaderboard_preview.append({
                    'user_id': user_id_key,
                    'name': 'Admin' if is_admin else 'Unknown User',
                    'attempted_questions': result['total_questions'],
                    'time_taken': round(result.get('total_time_taken', 0), 2),
                    'email': ADMIN_USERNAME if is_admin else '',
                    'phone': '',
                    'total_correct': result['total_correct'],
                    'total_questions': result['total_questions'],
                    'average_score': round(result['average_score'], 2)  # For sorting only
                })
                print(f"[Dashboard] Added {'admin' if is_admin else 'unknown'} user: {user_id_key} - {result['total_correct']}/{result['total_questions']}")
        
        # Add users who haven't taken any quiz yet
        for user_id_str, user in all_users_dict.items():
            if user_id_str not in processed_user_ids:
                leaderboard_preview.append({
                    'user_id': user_id_str,
                    'name': user.get('name', 'Unknown'),
                    'attempted_questions': 0,
                    'time_taken': 0.0,
                    'email': user.get('email', ''),
                    'phone': user.get('phone', ''),
                    'total_correct': 0,
                    'total_questions': 0,
                    'average_score': 0.0  # For sorting only
                })
                print(f"[Dashboard] Added user without quiz results: {user.get('name', 'Unknown')}")
        
        # Sort by average_score descending, then by time_taken ascending (less time is better)
        leaderboard_preview.sort(key=lambda x: (-x['average_score'], x['time_taken']))
        
        # Add rank to each entry and remove average_score from response
        for index, entry in enumerate(leaderboard_preview, start=1):
            entry['rank'] = index
            # Remove average_score from response (was only used for sorting)
            entry.pop('average_score', None)
        
        print("[Dashboard] Dashboard data fetched successfully")
        
        # Prepare response
        # Prevent negative counts when admin is present
        users_not_attended = total_users - users_attended
        if users_not_attended < 0:
            users_not_attended = 0

        response_data = {
            'status': True,
            'message': 'Dashboard data retrieved successfully',
            'data': {
                'total_users': total_users,
                'users_attended_quiz': users_attended,
                'users_not_attended': users_not_attended,
                'leaderboard_preview': leaderboard_preview
            }
        }
        
        print("[Dashboard] Returning dashboard data")
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"[Dashboard] ERROR: {str(e)}")
        return jsonify({
            'status': False,
            'error': str(e)
        }), 500

