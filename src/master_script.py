

def main():
    print('Master Script')
    print('')
    print('Options:')
    print('1) Hello World')
    print('2) Exit')

    while True:
        response = input('>> ')
        if response == '1':
            print('Hello World')
        elif response == '2':
            print('Goodbye')
            break
        else:
            print('Invalid option')


if __name__ == '__main__':
    main()
