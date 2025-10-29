from flask import Blueprint, request, jsonify
from config import db

get_quizzes_bp = Blueprint('get_quizzes', __name__)

@get_quizzes_bp.route('/quizzes', methods=['GET'])
def get_quizzes():
    try:
        # Check if database is connected
        if db is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get optional query parameters
        created_by = request.args.get('created_by')
        
        query = {}
        if created_by:
            query['created_by'] = created_by
        
        quizzes = db.quizzes.find(query).sort('created_at', -1)
        quiz_list = []
        for quiz in quizzes:
            quiz['_id'] = str(quiz['_id'])
            # Don't send correct answers in the list view
            for question in quiz['questions']:
                question.pop('correct_answer', None)
            quiz_list.append(quiz)
        
        return jsonify({
            'quizzes': quiz_list,
            'total': len(quiz_list)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

