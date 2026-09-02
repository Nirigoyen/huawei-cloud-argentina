import java.util.List;
import java.util.ArrayList;
import java.util.Optional;

public class UserService {
    private List<User> users = new ArrayList<>();

    public void addUser(User user) {
        users.add(user);
    }

    public Optional<User> findUser(String name) {
        return users.stream()
            .filter(u -> name.equals(u.getName()))
            .findFirst();
    }

    public Optional<String> getUserEmail(String name) {
        return findUser(name).map(User::getEmail);
    }

    public Optional<String> getUserCity(String name) {
        return findUser(name)
            .map(User::getAddress)
            .map(Address::getCity);
    }

    public String formatUserInfo(String name) {
        String email = getUserEmail(name).orElse("N/A");
        String city = getUserCity(name).orElse("Unknown");
        return name + " (" + email + ") from " + city;
    }
}

class User {
    private String name;
    private String email;
    private Address address;

    public User(String name, String email, Address address) {
        this.name = name;
        this.email = email;
        this.address = address;
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
    public Address getAddress() { return address; }
}

class Address {
    private String street;
    private String city;
    private String zipCode;

    public Address(String street, String city, String zipCode) {
        this.street = street;
        this.city = city;
        this.zipCode = zipCode;
    }

    public String getStreet() { return street; }
    public String getCity() { return city; }
    public String getZipCode() { return zipCode; }
}
