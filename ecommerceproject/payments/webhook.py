import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Payment
from .stripe_service import StripePaymentService
import stripe

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Stripe webhook handler for payment events.
    
    Handles the following Stripe events:
    - payment_intent.succeeded: Payment completed successfully
    - payment_intent.payment_failed: Payment failed
    - payment_intent.canceled: Payment was canceled
    
    Args:
        request: HTTP request containing Stripe webhook event
        
    Returns:
        JsonResponse with status and message
    """
    
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning("Webhook received without Stripe signature")
        return JsonResponse({
            'success': False,
            'error': 'Missing Stripe signature'
        }, status=400)
    
    try:
        # Verify webhook signature
        event = StripePaymentService.verify_webhook_signature(payload, sig_header)
        
        logger.info(f"Webhook event received: {event['type']}")
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            handle_payment_succeeded(event['data']['object'])
        
        elif event['type'] == 'payment_intent.payment_failed':
            handle_payment_failed(event['data']['object'])
        
        elif event['type'] == 'payment_intent.canceled':
            handle_payment_canceled(event['data']['object'])
        
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return JsonResponse({'success': True}, status=200)
    
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid Stripe signature: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Invalid signature'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def handle_payment_succeeded(payment_intent):
    """
    Handle successful payment event.
    
    Args:
        payment_intent: Stripe PaymentIntent object from webhook
    """
    try:
        payment_intent_id = payment_intent['id']
        
        # Find payment record
        try:
            payment = Payment.objects.get(transaction_id=payment_intent_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            return
        
        # Update payment status
        payment.status = 'success'
        payment.raw_response = {
            'stripe_status': payment_intent['status'],
            'amount': payment_intent['amount'] / 100,
            'currency': payment_intent['currency'],
            'client_secret': payment_intent['client_secret'],
            'charges': [charge['id'] for charge in payment_intent.get('charges', {}).get('data', [])],
        }
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'paid'
        order.save()
        
        logger.info(f"Payment {payment.id} updated to success status. Order {order.id} marked as paid.")
    
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")


def handle_payment_failed(payment_intent):
    """
    Handle failed payment event.
    
    Args:
        payment_intent: Stripe PaymentIntent object from webhook
    """
    try:
        payment_intent_id = payment_intent['id']
        
        # Find payment record
        try:
            payment = Payment.objects.get(transaction_id=payment_intent_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            return
        
        # Update payment status
        payment.status = 'failed'
        error_message = 'Unknown error'
        if payment_intent.get('last_payment_error'):
            error_message = payment_intent['last_payment_error'].get('message', 'Unknown error')
        
        payment.raw_response = {
            'stripe_status': payment_intent['status'],
            'error': error_message,
            'error_code': payment_intent.get('last_payment_error', {}).get('code'),
        }
        payment.save()
        
        # Keep order in pending status (user can retry)
        logger.warning(f"Payment {payment.id} failed: {error_message}")
    
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")


def handle_payment_canceled(payment_intent):
    """
    Handle canceled payment event.
    
    Args:
        payment_intent: Stripe PaymentIntent object from webhook
    """
    try:
        payment_intent_id = payment_intent['id']
        
        # Find payment record
        try:
            payment = Payment.objects.get(transaction_id=payment_intent_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment record not found for intent {payment_intent_id}")
            return
        
        # Update payment status
        payment.status = 'failed'
        payment.raw_response = {
            'stripe_status': payment_intent['status'],
            'error': 'Payment was canceled',
        }
        payment.save()
        
        logger.warning(f"Payment {payment.id} was canceled by user")
    
    except Exception as e:
        logger.error(f"Error handling payment cancellation: {str(e)}")
