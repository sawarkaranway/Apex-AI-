"""
REST API Endpoints for Scientific Calculator & Calculation History.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CalculationHistory
from agent.math_engine import parse_and_calculate


@api_view(['POST'])
@permission_classes([AllowAny])
def evaluate_math_endpoint(request):
    """
    Evaluates a mathematical expression or natural-language query deterministically
    and persists the result into calculation history.
    """
    query = request.data.get('query', '').strip()
    expression = request.data.get('expression', '').strip()

    if not query and not expression:
        return Response({
            'status': 'error',
            'error_type': 'invalid_input',
            'message': 'query or expression parameter is required.'
        }, status=status.HTTP_400_BAD_REQUEST)

    result = parse_and_calculate(query=query, explicit_expression=expression)

    # Persist in history if user is authenticated or guest
    try:
        user = request.user if request.user.is_authenticated else None
        CalculationHistory.objects.create(
            user=user,
            query=query or expression,
            operation=result.get('operation', 'general'),
            exact_answer=result.get('exact_answer', ''),
            approximate_answer=result.get('approximate_answer', ''),
            formula_used=result.get('formula_used', ''),
            steps=result.get('steps', []),
            result_json=result
        )
    except Exception:
        pass

    return Response(result)


@api_view(['GET', 'DELETE'])
@permission_classes([AllowAny])
def calculation_history_endpoint(request, item_id=None):
    """
    Lists calculation history with user isolation or clears history.
    """
    user = request.user if request.user.is_authenticated else None

    if request.method == 'GET':
        if user:
            history = CalculationHistory.objects.filter(user=user)[:50]
        else:
            history = CalculationHistory.objects.filter(user__isnull=True)[:50]

        data = [{
            'id': str(h.id),
            'query': h.query,
            'operation': h.operation,
            'exact_answer': h.exact_answer,
            'approximate_answer': h.approximate_answer,
            'formula_used': h.formula_used,
            'steps': h.steps,
            'result_json': h.result_json,
            'created_at': h.created_at.isoformat()
        } for h in history]
        return Response({'history': data})

    elif request.method == 'DELETE':
        if item_id:
            query_filter = {'id': item_id}
            if user:
                query_filter['user'] = user
            CalculationHistory.objects.filter(**query_filter).delete()
            return Response({'status': 'deleted', 'id': item_id})
        else:
            # Clear all history for current user
            if user:
                CalculationHistory.objects.filter(user=user).delete()
            else:
                CalculationHistory.objects.filter(user__isnull=True).delete()
            return Response({'status': 'cleared'})
