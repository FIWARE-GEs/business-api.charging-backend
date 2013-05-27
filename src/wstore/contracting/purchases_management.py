from datetime import datetime

from wstore.charging_engine.charging_engine import ChargingEngine
from wstore.models import Purchase
from wstore.models import UserProfile
from wstore import charging_engine
from wstore.contracting.purchase_rollback import PurchaseRollback


@PurchaseRollback
def create_purchase(user, offering, org_owned=False, payment_info=None):

    if offering.state != 'published':
        raise Exception("This offering can't be purchased")

    profile = UserProfile.objects.get(user=user)

    if offering.pk in profile.offerings_purchased or offering.pk in profile.organization.offerings_purchased:
        raise Exception('The offering has been already purchased')

    org = ''
    if org_owned:
        organization = profile.organization
        org = organization.name

    # Get the effective tax address
    if not 'tax_address' in payment_info:
        if org_owned:
            tax = organization.tax_address
        else:
            tax = profile.tax_address

        # Check that the customer has a tax address
        if not 'street' in tax:
            raise Exception('The customer does not have a tax address')
    else:
        tax = payment_info['tax_address']

        # Check tax_address fields
        if (not 'street' in tax) or (not 'postal' in tax) or (not 'city' in tax) or (not 'country' in tax):
            raise Exception('The tax address is not valid')

    # Check the payment method before purchase creation in order to avoid
    # an inconsistent state in the database
    credit_card_info = None
    if payment_info['payment_method'] == 'credit_card':
        if 'credit_card' in payment_info:
            # Check credit card info
            if (not ('number' in payment_info['credit_card'])) or (not ('type' in payment_info['credit_card']))\
            or (not ('expire_year' in payment_info['credit_card'])) or (not ('expire_month' in payment_info['credit_card']))\
            or (not ('cvv2' in payment_info['credit_card'])):
                raise Exception('Invalid credit card info')

            credit_card_info = payment_info['credit_card']
        else:
            if org_owned:
                credit_card_info = organization.payment_info
            else:
                credit_card_info = profile.payment_info

            # Check the credit card info
            if not 'number' in credit_card_info:
                raise Exception('The customer does not have payment info')

    elif payment_info['payment_method'] != 'paypal':
        raise Exception('Invalid payment method')

    # Create the purchase
    purchase = Purchase.objects.create(
        customer=user,
        date=datetime.now(),
        offering=offering,
        owner_organization=org,
        organization_owned=org_owned,
        state='pending',
        tax_address=tax
    )
    # Load ref
    purchase.ref = purchase.pk
    purchase.save()

    if credit_card_info != None:
        charging_engine = ChargingEngine(purchase, payment_method='credit_card', credit_card=credit_card_info)
    else:
        charging_engine = ChargingEngine(purchase, payment_method='paypal')

    redirect_url = charging_engine.resolve_charging(new_purchase=True)

    if redirect_url == None:
        result = purchase

        # If no redirect URL is provided the purchase has ended so the user profile
        # info is updated
        profile.offerings_purchased.append(offering.pk)
        profile.save()

        if org_owned:
            organization.offerings_purchased.append(offering.pk)
            organization.save()

    else:
        result = redirect_url

    return result