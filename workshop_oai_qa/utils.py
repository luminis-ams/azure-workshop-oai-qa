from langchain.schema import BaseMessage, ChatMessage, AIMessage


def role_from_message(message: BaseMessage):
    """
    Extract role from Typed Langchain Messages
    :param message:
    :return:
    """
    if isinstance(message, ChatMessage):
        return message.role
    elif isinstance(message, AIMessage):
        return 'assistant'
    else:
        raise ValueError(f'Unexpected message type: {type(message)}')
