import stripe
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)

# Initialize Stripe with API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service to handle Stripe payment operations"""
    
    CURRENCY = 'bdt'  # Currency for all transactions
    
    @staticmethod
    def create_payment_intent(order):
        """
        Create a Stripe payment intent for an order.
        
        Args:
            order: Order instance
            
        Returns:
            dict: Payment intent details with client_secret
        """
        try:

            amount = float(order.total_amount)
            
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=StripePaymentService.CURRENCY,
                metadata={
                    'order_id': order.id,
                    'user_email': order.user.email,
                    'user_id': order.user.id,
                },
                description=f'Payment for Order #{order.id}',
            )
            
            logger.info(f"Payment intent created: {intent.id} for Order #{order.id}")
            
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': float(order.total_amount),
                'currency': StripePaymentService.CURRENCY,
                'status': intent.status,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error while creating payment intent: {str(e)}")
            raise Exception(f"Payment intent creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while creating payment intent: {str(e)}")
            raise Exception(f"Payment intent creation failed: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(payload, sig_header):
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise Exception(f"Invalid webhook signature: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error verifying webhook: {str(e)}")
            raise Exception(f"Webhook verification failed: {str(e)}")
