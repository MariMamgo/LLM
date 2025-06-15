import google.generativeai as genai
import json
from typing import Dict, List, Any

class PizzaOrderingSystem:
    def __init__(self):
        API_KEY = "AIzaSyAIu8sBTvcURlDf1dAPs8sIo1CmXc2fnz0"
        genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.order_data = {
            'items': [],
            'customer_info': {},
            'total_price': 0.0
        }
        
        # Pizza menu with prices and toppings
        self.menu = {
            'pizzas': {
                'custom': {'price': 10.99, 'description': 'Build your own pizza with your choice of toppings', 'toppings': ['tomato sauce', 'mozzarella']},
                'margarita': {'price': 12.99, 'description': 'Classic tomato sauce, mozzarella, basil', 'toppings': ['tomato sauce', 'mozzarella', 'basil']},
                'pepperoni': {'price': 14.99, 'description': 'Tomato sauce, mozzarella, pepperoni', 'toppings': ['tomato sauce', 'mozzarella', 'pepperoni']},
                'hawaian': {'price': 15.99, 'description': 'Tomato sauce, mozzarella, ham, pineapple', 'toppings': ['tomato sauce', 'mozzarella', 'ham', 'pineapple']},
                'veggie': {'price': 16.99, 'description': 'Tomato sauce, mozzarella, bell peppers, mushrooms, onions', 'toppings': ['tomato sauce', 'mozzarella', 'bell peppers', 'mushrooms', 'onions']},
                'meat_lovers': {'price': 18.99, 'description': 'Tomato sauce, mozzarella, pepperoni, sausage, ham, bacon', 'toppings': ['tomato sauce', 'mozzarella', 'pepperoni', 'sausage', 'ham', 'bacon']},
                'bbq_chicken': {'price': 17.99, 'description': 'BBQ sauce, mozzarella, grilled chicken, red onions', 'toppings': ['bbq sauce', 'mozzarella', 'grilled chicken', 'red onions']}
            },
            'sizes': {
                'small': {'multiplier': 0.8, 'description': '10 inch'},
                'medium': {'multiplier': 1.0, 'description': '12 inch'},
                'large': {'multiplier': 1.3, 'description': '14 inch'},
                'xl': {'multiplier': 1.6, 'description': '16 inch'}
            },
            'sides': {
                'garlic_bread': {'price': 5.99, 'description': 'Fresh baked garlic bread'},
                'chicken_wings': {'price': 8.99, 'description': '8 piece chicken wings'},
                'caesar_salad': {'price': 7.99, 'description': 'Fresh caesar salad'},
                'soda': {'price': 2.99, 'description': 'Coca-Cola, Pepsi, Sprite'}
            },
            'toppings': {
                'extra_cheese': {'price': 2.00},
                'pepperoni': {'price': 1.50},
                'sausage': {'price': 1.50},
                'mushrooms': {'price': 1.00},
                'onions': {'price': 1.00},
                'bell_peppers': {'price': 1.00},
                'pineapple': {'price': 1.50},
                'ham': {'price': 1.50},
                'bacon': {'price': 2.00},
                'grilled_chicken': {'price': 2.50},
                'basil': {'price': 1.00}
            }
        }
    
    def get_menu(self) -> Dict[str, Any]:
        """Function to get the current menu"""
        return self.menu
    
    def add_pizza_to_order(self, pizza_type: str, size: str, quantity: int = 1, extra_toppings: List[str] = None, remove_toppings: List[str] = None) -> Dict[str, Any]:
        """Function to add pizza to order with optional topping modifications"""
        pizza_type = pizza_type.lower().replace(' ', '_')
        size = size.lower()
        extra_toppings = extra_toppings or []
        remove_toppings = remove_toppings or []

        if pizza_type not in self.menu['pizzas']:
            return {'success': False, 'message': f'Pizza type "{pizza_type}" not available 😢'}
        
        if size not in self.menu['sizes']:
            return {'success': False, 'message': f'Size "{size}" not available 😕'}

        # Validate toppings
        invalid_toppings = [t for t in extra_toppings + remove_toppings if t not in self.menu['toppings']]
        if invalid_toppings:
            return {'success': False, 'message': f'Invalid toppings: {", ".join(invalid_toppings)} 🙅‍♂️'}

        # Check if removable toppings are on the pizza
        pizza_toppings = self.menu['pizzas'][pizza_type]['toppings']
        non_removable = [t for t in remove_toppings if t not in pizza_toppings]
        if non_removable:
            return {'success': False, 'message': f'Cannot remove {", ".join(non_removable)} from {pizza_type} as they are not included 🚫'}

        # Calculate price
        base_price = self.menu['pizzas'][pizza_type]['price']
        size_multiplier = self.menu['sizes'][size]['multiplier']
        toppings_price = sum(self.menu['toppings'][t]['price'] for t in extra_toppings)
        total_price = (base_price + toppings_price) * size_multiplier * quantity

        # Update toppings list
        final_toppings = [t for t in pizza_toppings if t not in remove_toppings] + extra_toppings

        item = {
            'type': 'pizza',
            'name': pizza_type,
            'size': size,
            'quantity': quantity,
            'unit_price': (base_price + toppings_price) * size_multiplier,
            'total_price': total_price,
            'toppings': final_toppings,
            'added_toppings': extra_toppings,
            'removed_toppings': remove_toppings
        }
        
        self.order_data['items'].append(item)
        self.order_data['total_price'] += total_price
        
        return {
            'success': True, 
            'message': f'Added {quantity}x {size} {pizza_type} pizza(s) to order with toppings: {", ".join(final_toppings)} 🍕',
            'item': item
        }
    
    def create_custom_pizza(self, size: str, toppings: List[str], quantity: int = 1) -> Dict[str, Any]:
        """Create a custom pizza with specified toppings"""
        size = size.lower()
        toppings = toppings or ['tomato sauce', 'mozzarella']  # Default toppings

        if size not in self.menu['sizes']:
            return {'success': False, 'message': f'Size "{size}" not available 😕'}

        # Validate toppings
        invalid_toppings = [t for t in toppings if t not in self.menu['toppings']]
        if invalid_toppings:
            return {'success': False, 'message': f'Invalid toppings: {", ".join(invalid_toppings)} 🙅‍♂️'}

        # Calculate price
        base_price = self.menu['pizzas']['custom']['price']
        size_multiplier = self.menu['sizes'][size]['multiplier']
        toppings_price = sum(self.menu['toppings'][t]['price'] for t in toppings)
        total_price = (base_price + toppings_price) * size_multiplier * quantity

        item = {
            'type': 'pizza',
            'name': 'custom',
            'size': size,
            'quantity': quantity,
            'unit_price': (base_price + toppings_price) * size_multiplier,
            'total_price': total_price,
            'toppings': toppings,
            'added_toppings': toppings,
            'removed_toppings': []
        }

        self.order_data['items'].append(item)
        self.order_data['total_price'] += total_price

        return {
            'success': True,
            'message': f'Added {quantity}x {size} custom pizza(s) with toppings: {", ".join(toppings)} 🍕',
            'item': item
        }
    
    def add_side_to_order(self, side_name: str, quantity: int = 1) -> Dict[str, Any]:
        """Function to add sides to order"""
        side_name = side_name.lower().replace(' ', '_')
        
        if side_name not in self.menu['sides']:
            return {'success': False, 'message': f'Side "{side_name}" not available 😢'}
        
        unit_price = self.menu['sides'][side_name]['price']
        total_price = unit_price * quantity
        
        item = {
            'type': 'side',
            'name': side_name,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price
        }
        
        self.order_data['items'].append(item)
        self.order_data['total_price'] += total_price
        
        return {
            'success': True,
            'message': f'Added {quantity}x {side_name} to order 🍟',
            'item': item
        }
    
    def remove_item_from_order(self, item_index: int) -> Dict[str, Any]:
        """Function to remove item from order"""
        if 0 <= item_index < len(self.order_data['items']):
            removed_item = self.order_data['items'].pop(item_index)
            self.order_data['total_price'] -= removed_item['total_price']
            return {'success': True, 'message': f'Removed {removed_item["name"]} from order 🗑️'}
        else:
            return {'success': False, 'message': 'Invalid item index 😕'}
    
    def modify_toppings(self, item_index: int, add_toppings: List[str] = None, remove_toppings: List[str] = None) -> Dict[str, Any]:
        """Modify toppings for an existing pizza in the order"""
        add_toppings = add_toppings or []
        remove_toppings = remove_toppings or []

        if not (0 <= item_index < len(self.order_data['items'])):
            return {'success': False, 'message': 'Invalid item index 😕'}

        item = self.order_data['items'][item_index]
        if item['type'] != 'pizza':
            return {'success': False, 'message': 'Can only modify toppings for pizzas 🍕'}

        # Validate toppings
        invalid_toppings = [t for t in add_toppings + remove_toppings if t not in self.menu['toppings']]
        if invalid_toppings:
            return {'success': False, 'message': f'Invalid toppings: {", ".join(invalid_toppings)} 🙅‍♂️'}

        # Check if removable toppings are on the pizza
        current_toppings = item['toppings']
        non_removable = [t for t in remove_toppings if t not in current_toppings]
        if non_removable:
            return {'success': False, 'message': f'Cannot remove {", ".join(non_removable)} as they are not on this pizza 🚫'}

        # Update price
        old_toppings_price = sum(self.menu['toppings'][t]['price'] for t in item['added_toppings'])
        new_toppings_price = sum(self.menu['toppings'][t]['price'] for t in add_toppings)
        base_price = self.menu['pizzas'][item['name']]['price']
        size_multiplier = self.menu['sizes'][item['size']]['multiplier']
        self.order_data['total_price'] -= item['total_price']
        item['total_price'] = (base_price + new_toppings_price) * size_multiplier * item['quantity']
        self.order_data['total_price'] += item['total_price']

        # Update toppings
        item['toppings'] = [t for t in current_toppings if t not in remove_toppings] + add_toppings
        item['added_toppings'] = add_toppings
        item['removed_toppings'] = remove_toppings

        return {
            'success': True,
            'message': f'Updated toppings for {item["name"]} pizza: {", ".join(item["toppings"])} 🧀'
        }
    
    def get_current_order(self) -> Dict[str, Any]:
        """Function to get current order details"""
        return self.order_data
    
    def set_customer_info(self, name: str, phone: str, address: str) -> Dict[str, Any]:
        """Function to set customer information"""
        self.order_data['customer_info'] = {
            'name': name,
            'phone': phone,
            'address': address
        }
        return {'success': True, 'message': 'Customer information updated 📋'}
    
    def finalize_order(self) -> Dict[str, Any]:
        """Function to finalize the order"""
        if not self.order_data['items']:
            return {'success': False, 'message': 'No items in order 😢'}
        
        if not self.order_data['customer_info']:
            return {'success': False, 'message': 'Customer information required 📋'}
        
        # Add tax (8%)
        tax = self.order_data['total_price'] * 0.08
        final_total = self.order_data['total_price'] + tax
        
        order_summary = {
            'order_id': f'ORD{hash(str(self.order_data)) % 10000:04d}',
            'items': self.order_data['items'],
            'customer_info': self.order_data['customer_info'],
            'subtotal': self.order_data['total_price'],
            'tax': tax,
            'total': final_total,
            'estimated_delivery': '30-45 minutes'
        }
        
        return {'success': True, 'message': 'Order finalized successfully! 🎉', 'order': order_summary}
    
    def get_function_declarations(self):
        """Get function declarations for Gemini API"""
        return [
            {
                'name': 'get_menu',
                'description': 'Get the current pizza menu with prices and toppings',
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'add_pizza_to_order',
                'description': 'Add a pizza to the current order with optional topping modifications',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'pizza_type': {
                            'type': 'string',
                            'description': 'Type of pizza (custom, margarita, pepperoni, hawaian, veggie, meat_lovers, bbq_chicken)'
                        },
                        'size': {
                            'type': 'string',
                            'description': 'Size of pizza (small, medium, large, xl)'
                        },
                        'quantity': {
                            'type': 'integer',
                            'description': 'Number of pizzas (default: 1)'
                        },
                        'extra_toppings': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of extra toppings to add'
                        },
                        'remove_toppings': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of toppings to remove'
                        }
                    },
                    'required': ['pizza_type', 'size']
                }
            },
            {
                'name': 'create_custom_pizza',
                'description': 'Create a custom pizza with specified toppings',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'size': {
                            'type': 'string',
                            'description': 'Size of pizza (small, medium, large, xl)'
                        },
                        'toppings': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of toppings for the custom pizza'
                        },
                        'quantity': {
                            'type': 'integer',
                            'description': 'Number of pizzas (default: 1)'
                        }
                    },
                    'required': ['size', 'toppings']
                }
            },
            {
                'name': 'add_side_to_order',
                'description': 'Add sides or drinks to the order',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'side_name': {
                            'type': 'string',
                            'description': 'Name of side item (garlic_bread, chicken_wings, caesar_salad, soda)'
                        },
                        'quantity': {
                            'type': 'integer',
                            'description': 'Number of side items (default: 1)'
                        }
                    },
                    'required': ['side_name']
                }
            },
            {
                'name': 'remove_item_from_order',
                'description': 'Remove an item from the current order',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'item_index': {
                            'type': 'integer',
                            'description': 'Index of item to remove from order'
                        }
                    },
                    'required': ['item_index']
                }
            },
            {
                'name': 'modify_toppings',
                'description': 'Modify toppings for an existing pizza in the order',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'item_index': {
                            'type': 'integer',
                            'description': 'Index of the pizza in the order to modify'
                        },
                        'add_toppings': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of toppings to add'
                        },
                        'remove_toppings': {
                            'type': 'array',
                            'items': {'type': 'string'},
                            'description': 'List of toppings to remove'
                        }
                    },
                    'required': ['item_index']
                }
            },
            {
                'name': 'get_current_order',
                'description': 'Get the current order details and total',
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            },
            {
                'name': 'set_customer_info',
                'description': 'Set customer information for delivery',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': 'Customer name'
                        },
                        'phone': {
                            'type': 'string',
                            'description': 'Customer phone number'
                        },
                        'address': {
                            'type': 'string',
                            'description': 'Delivery address'
                        }
                    },
                    'required': ['name', 'phone', 'address']
                }
            },
            {
                'name': 'finalize_order',
                'description': 'Finalize the order and get order confirmation',
                'parameters': {
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            }
        ]
    
    def execute_function(self, function_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a function call"""
        if function_name == 'get_menu':
            return self.get_menu()
        elif function_name == 'add_pizza_to_order':
            return self.add_pizza_to_order(**parameters)
        elif function_name == 'create_custom_pizza':
            return self.create_custom_pizza(**parameters)
        elif function_name == 'add_side_to_order':
            return self.add_side_to_order(**parameters)
        elif function_name == 'remove_item_from_order':
            return self.remove_item_from_order(**parameters)
        elif function_name == 'modify_toppings':
            return self.modify_toppings(**parameters)
        elif function_name == 'get_current_order':
            return self.get_current_order()
        elif function_name == 'set_customer_info':
            return self.set_customer_info(**parameters)
        elif function_name == 'finalize_order':
            return self.finalize_order()
        else:
            return {'success': False, 'message': f'Unknown function: {function_name} 😕'}
    
    def chat(self):
        """Main chat loop"""
        print("🍕✨ Welcome to Mamgo's Pizza, cutie! I'm your friendly AI pizza buddy! 🤖💕")
        print("Craving something cheesy or crispy? You can:")
        print("- Check our menu 🍕")
        print("- Order pizzas or sides 🍟")
        print("- Customize toppings (add/remove) 🧀")
        print("- Create your own custom pizza 🌟")
        print("Just tell me what sounds yummy! Type 'quit' to say bye-bye! 👋😢\n")

        system_prompt = """You are a friendly pizza ordering assistant for Mamgo's Pizza. 
        Use the available functions to help customers:
        - Show menu with get_menu
        - Add pizzas with add_pizza_to_order (supports extra_toppings and remove_toppings)
        - Create custom pizzas with create_custom_pizza
        - Modify toppings with modify_toppings
        - Add sides with add_side_to_order
        - Remove items with remove_item_from_order
        - Collect customer info with set_customer_info
        - Finalize orders with finalize_order
        
        Always be helpful, friendly, and confirm details. Use emojis to keep it fun! 😊🍕
        When customers ask about the menu, use get_menu.
        For adding items, ask for quantity if not specified (default to 1).
        For pizzas, ask if they want to add/remove toppings or create a custom pizza.
        Show the current order total after adding items.
        """
        
        chat = self.model.start_chat()
        try:
            chat.send_message(system_prompt)
        except:
            pass
        
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Thanks for visiting Mamgo's Pizza! Come back soon! 🍕😘")
                break
            
            if not user_input:
                continue
            
            try:
                response = chat.send_message(
                    user_input,
                    tools=[{'function_declarations': self.get_function_declarations()}]
                )
                
                if (response.candidates and 
                    len(response.candidates) > 0 and 
                    response.candidates[0].content and 
                    response.candidates[0].content.parts):
                    
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            func_call = part.function_call
                            func_name = func_call.name
                            func_args = dict(func_call.args) if func_call.args else {}
                            
                            result = self.execute_function(func_name, func_args)
                            
                            try:
                                response = chat.send_message([
                                    genai.protos.Part(
                                        function_response=genai.protos.FunctionResponse(
                                            name=func_name,
                                            response={'result': result}
                                        )
                                    )
                                ])
                            except Exception as e:
                                print(f"Function response error: {e} 😕")
                                response = chat.send_message(f"Function {func_name} executed with result: {result}")
                
                if hasattr(response, 'text') and response.text:
                    print(f"Assistant: {response.text}\n")
                elif response.candidates and response.candidates[0].content:
                    text_parts = []
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        print(f"Assistant: {''.join(text_parts)}\n")
                    else:
                        print("Assistant: I'm here to help you order pizza! What would you like? 🍕\n")
                else:
                    print("Assistant: I'm here to help you order pizza! What would you like? 🍕\n")
                
            except Exception as e:
                print(f"Error: {e} 😕")
                try:
                    fallback_response = chat.send_message(f"Please help the customer who said: {user_input}")
                    if hasattr(fallback_response, 'text') and fallback_response.text:
                        print(f"Assistant: {fallback_response.text}\n")
                    else:
                        print("Assistant: I'm here to help you order pizza! You can ask about our menu or tell me what you'd like to order. 🍕\n")
                except:
                    print("Assistant: I'm here to help you order pizza! You can ask about our menu or tell me what you'd like to order. 🍕\n")

def main():
    pizza_system = PizzaOrderingSystem()
    pizza_system.chat()

if __name__ == "__main__":
    main()