from flask import Blueprint, jsonify
from bson import ObjectId
from config import db
from utils.auth import admin_required

quiz_info_bp = Blueprint('quiz_info', __name__)

@quiz_info_bp.route('/quiz_info/<user_id>', methods=['GET'])
@admin_required
def get_quiz_info(user_id):
    """
    Get all quiz information for a specific user
    Returns all quizzes the user has attempted with their answers
    """
    try:
        print(f"[Quiz Info] Fetching quiz information for user_id: {user_id}")
        
        # Check if database is connected
        if db is None:
            print("[Quiz Info] ERROR: Database connection failed")
            return jsonify({
                'status': False,
                'error': 'Database connection failed'
            }), 500
        
        # Fetch user details to verify user exists (unless it's admin)
        user = None
        if user_id.lower() != 'admin':
            try:
                if ObjectId.is_valid(user_id):
                    user = db.users.find_one({'_id': ObjectId(user_id)}, {'password': 0})
                else:
                    print(f"[Quiz Info] Invalid user_id format: {user_id}")
                    return jsonify({
                        'status': False,
                        'error': 'Invalid user ID format'
                    }), 400
            except Exception as e:
                print(f"[Quiz Info] Error fetching user: {str(e)}")
                return jsonify({
                    'status': False,
                    'error': 'User not found'
                }), 404
        
        # Get all quiz results for this user
        print(f"[Quiz Info] Fetching quiz results for user_id: {user_id}")
        quiz_results = list(db.quiz_results.find({'user_id': user_id}).sort('submitted_at', -1))
        
        if not quiz_results:
            print(f"[Quiz Info] No quiz results found for user_id: {user_id}")
            user_info = {
                'user_id': user_id,
                'name': user.get('name', 'Admin') if user else 'Admin' if user_id.lower() == 'admin' else 'Unknown',
                'email': user.get('email', '') if user else '',
                'total_quizzes_attempted': 0
            }
            return jsonify({
                'status': True,
                'message': 'No quiz attempts found for this user',
                'user_info': user_info,
                'quizzes': []
            }), 200
        
        print(f"[Quiz Info] Found {len(quiz_results)} quiz results")
        
        # Prepare user info
        user_info = {
            'user_id': user_id,
            'name': user.get('name', 'Admin') if user else 'Admin' if user_id.lower() == 'admin' else 'Unknown',
            'email': user.get('email', '') if user else '',
            'total_quizzes_attempted': len(quiz_results)
        }
        
        # Process each quiz result
        quizzes_info = []
        for result in quiz_results:
            quiz_id = result.get('quiz_id', '')
            
            # Clean quiz_id (remove trailing comma if present)
            quiz_id_clean = quiz_id.rstrip(',') if quiz_id else ''
            
            # Fetch full quiz details
            quiz_details = None
            if quiz_id_clean and ObjectId.is_valid(quiz_id_clean):
                try:
                    quiz_details = db.quizzes.find_one({'_id': ObjectId(quiz_id_clean)})
                    print(f"[Quiz Info] Fetched quiz details for quiz_id: {quiz_id_clean}")
                except Exception as e:
                    print(f"[Quiz Info] Error fetching quiz {quiz_id_clean}: {str(e)}")
            elif quiz_id_clean:
                print(f"[Quiz Info] Invalid quiz_id format: {quiz_id_clean}")
            
            # Build quiz info with user's answers
            quiz_info = {
                'quiz_id': quiz_id_clean if quiz_id_clean else quiz_id,
                'quiz_title': quiz_details.get('title', 'Unknown Quiz') if quiz_details else 'Unknown Quiz',
                'quiz_description': quiz_details.get('description', '') if quiz_details else '',
                'submitted_at': result.get('submitted_at', ''),
                'time_taken': result.get('time_taken', 0),
                'correct_answers': result.get('correct_answers', 0),
                'total_questions': result.get('total_questions', 0),
                'score_percentage': round((result.get('correct_answers', 0) / result.get('total_questions', 1) * 100), 2) if result.get('total_questions', 0) > 0 else 0,
                'questions': []
            }
            
            # Add questions with user's answers
            result_questions = result.get('questions', [])
            for question_data in result_questions:
                question_info = {
                    'question_id': question_data.get('question_id', ''),
                    'options': question_data.get('options', []),
                    'correct_answer': question_data.get('correct_answer', ''),
                    'user_answer': question_data.get('user_answer', ''),
                    'is_correct': question_data.get('is_correct', False)
                }
                quiz_info['questions'].append(question_info)
            
            quizzes_info.append(quiz_info)
            print(f"[Quiz Info] Added quiz info: {quiz_info['quiz_title']} - {quiz_info['correct_answers']}/{quiz_info['total_questions']}")
        
        print(f"[Quiz Info] Successfully compiled quiz information for user_id: {user_id}")
        
        return jsonify({
            'status': True,
            'message': 'Quiz information retrieved successfully',
            'user_info': user_info,
            'quizzes': quizzes_info
        }), 200
        
    except Exception as e:
        print(f"[Quiz Info] ERROR: {str(e)}")
        return jsonify({
            'status': False,
            'error': str(e)
        }), 500

