import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment
from products.models import Product

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def reduce_stock_on_successful_payment(sender, instance, created, update_fields, **kwargs):

    if created:
        return 
    
    if instance.status == 'success':

        if update_fields and 'status' not in update_fields:
            return
        
        try:
            order = instance.order

            order_items = order.items.all()
            
            for item in order_items:
                product = item.product
                
                # Reduce product stock by order item quantity
                if product.stock >= item.quantity:
                    product.stock -= item.quantity
                    product.save()
                    logger.info(
                        f"Stock reduced for product {product.id} ({product.name}). "
                        f"Quantity: {item.quantity}, Remaining stock: {product.stock}"
                    )
                else:
                    logger.warning(
                        f"Insufficient stock for product {product.id} ({product.name}). "
                        f"Required: {item.quantity}, Available: {product.stock}"
                    )
            
            logger.info(f"Stock reduction completed for order {order.id}")
            
        except Exception as e:
            logger.error(f"Error reducing stock for payment {instance.id}: {str(e)}")
            # Don't raise exception to prevent payment creation failure


def ready():
    """
    This function is called when the app is ready.
    Import signals here to ensure they are registered.
    """
    pass
