from flask import Blueprint, request, jsonify
from config import db

get_all_quizzes_detailed_bp = Blueprint('get_all_quizzes_detailed', __name__)

@get_all_quizzes_detailed_bp.route('/quizzes/all', methods=['GET'])
def get_all_quizzes_detailed():
    """
    Get all quizzes with complete information including quiz ID and all details
    Includes correct answers
    """
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'status': False, 'error': 'Database connection failed'}), 500
        
        # Get optional query parameters
        created_by = request.args.get('created_by')
        
        query = {}
        if created_by:
            query['created_by'] = created_by
        
        # Fetch all quizzes with complete information
        quizzes = db.quizzes.find(query).sort('created_at', -1)
        quiz_list = []
        
        for quiz in quizzes:
            # Convert ObjectId to string
            quiz['_id'] = str(quiz['_id'])
            # Include all information including correct answers
            quiz_list.append(quiz)
        
        return jsonify({
            'status': True,
            'quizzes': quiz_list,
            'total': len(quiz_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': False,
            'error': str(e)
        }), 500

